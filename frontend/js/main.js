let socket = new WebSocket(
    `ws://${window.location.host}/ws`
);
const authorList = ["dxhFantasy", "lwjyreq"]
let authorCache = new Array();
let deployState = {
    active : false,
    card_index : -1,
    card_element : null,
}
async function getAuthor(){
    let cache = localStorage.getItem("authors")
    if (cache) {
        authorCache = JSON.parse(cache)
        return;
    }
    if(authorCache.length > 0){
        return authorCache;
    }
    for(const authorId of authorList){
        let response = await fetch(
            `https://api.github.com/users/${authorId}`
        );
        if(response.ok){
            let authorData = await response.json();
            authorCache.push(authorData);
        }
    }
    localStorage.setItem(
        "authors",
        JSON.stringify(authorCache)
    );
    return authorCache;
}

$("#start-room-button").click(() => {
    socket.send(
        JSON.stringify({
            action: "create_room",
        })
    )
})

$("#join-room-button").click(() => {
    showJoinRoomUI();
    $("#join-room-id").focus();
})

$("#about-button").click(() => {
    showAboutUI();
})
$("#join-room-confirm-button").click(() => {
    let roomId = $("#join-room-id").val();
    if( roomId.length === 0 ) {
        showNotice("请输入房间号", "warning");
        return;
    }
    socket.send(
        JSON.stringify({
            action: "join_room",
            room_id: roomId,
        })
    )
    hideJoinRoomUI();
})

$("#return-menu-button").click(() => {
    hideExitRoomUI();
    $("#menu").removeClass("hidden");
    $("#game").addClass("hidden");
});
$("#ready-button").click(() => {
    socket.send(
        JSON.stringify({
            action: "ready",
        })
    )
    $("#ready-button")
        .prop("disabled",true)
        .text("已准备");
})
$("#about-return").click(() => {
    hideAboutUI()
})
function cancelDeploy() {

    deployState.active = false;
    deployState.card_index = -1;
    deployState.card_element = null;

    $(".expanded-card")
        .removeClass("selected")
        .removeClass("hidden");

    $(".deployable")
        .removeClass("deployable");

    $("#hand-overlay")
        .removeClass("deploy-mode");

    $("#close-hand")
        .removeClass("hidden");

    $("#end-turn-button")
        .removeClass("hidden");
    console.log("取消部署");
}
function enterDeploy(card_element) {
    deployState.active = true;
    deployState.card_element = card_element;
    deployState.card_index =
        Number(card_element.attr("data-index"));
    console.log(card_element.attr("data-index"))
    $(".expanded-card")
        .not(card_element)
        .addClass("hidden");
    card_element.addClass("selected");
    $("#hand-overlay")
        .addClass("deploy-mode");
    $("#player-base-units")
        .addClass("deployable");
    $("#close-hand")
        .addClass("hidden");
    $("#end-turn-button")
        .addClass("hidden");
}
$(document).on("click", ".expanded-card", function(e){
    console.log("click card");
    e.stopPropagation();
    let card = $(this);
    if(card.hasClass("selected")){
        card.removeClass("selected");
        cancelDeploy();
        return;
    }
    if (deployState.active){
        cancelDeploy();
    }
    enterDeploy(card);
})
$(document).on("click", "#player-base-units", function() {
    console.log("点击了玩家基地");
    if (!deployState.active) {
        return;
    }
    console.log("请求部署单位");
    console.log("deployState:", deployState);
    socket.send(JSON.stringify({
        action: "player_operation",
        op_type: "deploy_unit",
        card_index: deployState.card_index,
        target: "player_base"
    }));

});
$(document).on("click", "#end-turn-button", function() {
    socket.send(JSON.stringify({
        action: "player_operation",
        op_type: "end_turn"
    }));
});
socket.onmessage = (event) => {
    let data = JSON.parse(event.data);
    console.log("Received message:", data);
    if( data.type === "room_created" ) {
        let roomId = data.room_id;
        showRoomUI(roomId);
    }
    if (data.type === "game_start") {
        showNotice("游戏已开始", "success");

        enterGame()
    }
    if (data.type === "opponent_left")  {
        showExitRoomUI();
    }
    if (data.type === "ready_check") {
        showReadyCheckUI();
    }
    if (data.type === "update_countdown") {
        $("#countdown").text(data.countdown);
    }
    if (data.type === "error"){
        showNotice(data.message, "warning")

        if (deployState.active) {
            cancelDeploy();
        }
    }
    if (data.type === "show_message") {
        console.log("Battle message:", data.message)
        showBattleMessage(data.message)
    }
    if (data.type === "update_state") {
        updateGameState(data)

        if (deployState.active){
            cancelDeploy()
        }
    }
}
function renderUnits(units, container){
    console.log(units)
    container.empty()
    units.map((unit, unit_idx) => {
        let info = cardInfo[unit.cardId]
        let element = $(`
            <div class="battle-unit" unit-idx=${unit_idx}>
                <div class="unit-action-cost">
                    ${unit.actionCost}
                </div>
                <div class="unit-name">
                    ${info.name}
                </div>
                <div class="unit-image">
                    <img src="assets/cards/${unit.card_id}.jpg">
                </div>
                <div class="unit-stats">
                    <span class="attack">
                        ${unit.atk}
                    </span>

                    <span class="hp">
                        ${unit.dfns}
                    </span>
                </div>

            </div>
        `)

        container.append(element)
    })
}
function renderBattlefield(cur_bf) {
    let frontlines = cur_bf.frontlines
    const containers = [
        $("#player-base-units"),
        $("frontline-units"),
        $("#enemy-base-units"),
    ]
    containers.map((container, idx) => {
        renderUnits(frontlines[idx].targets, container);
    })
}
function updateGameState(stateData) {
    if(deployState.active){
        cancelDeploy();
    }

    console.log("Updating game state:", stateData);
    $("#my-act-point").text(`行动点: ${stateData.my_act_point}`);
    $("#enemy-act-point").text(`行动点: ${stateData.enemy_act_point}`);
    $("#my-hq-hp").text(`HP: ${stateData.my_hq}`);
    $("#enemy-hq-hp").text(`HP: ${stateData.enemy_hq}`);
    $("#my-deck-counts").text(`${stateData.my_deck_cnts}`)
    $("#enemy-deck-counts").text(`${stateData.enemy_deck_counts}`)
    renderCompactHand(stateData.my_handcards);
    renderExpandedHand(stateData.my_handcards);
    renderEnemyHand(stateData.enemy_hc_counts);
    renderBattlefield(stateData.battlefields[stateData.cur_bf]);
}
function enterGame() {
    $("#menu").addClass("hidden");
    $("#room-modal").removeClass("active");
    $("#game").removeClass("hidden");
    $("#ready-modal").removeClass("active");
}

const jobs = {
    "dxhFantasy": "主策划/游戏设计",
    "lwjyreq": "前端网页/联机功能",
    "🌙 moon": "美术设计",
    "箐川" : "卡牌设计"
}
$("#player-hand").click(function(){
    $("#hand-overlay")
        .addClass("active");
});
$("#close-hand").click(function(){
    $("#hand-overlay")
        .removeClass("active");
});
$(document).ready(() => {
    getAuthor().then(() => {
        authorCache.forEach((author) => {
            let authorItem = `
            <li class="author-item">

            <img 
                src="${author.avatar_url}" 
                class="rounded-circle"
                width=60
                height=60
                alt="${author.login}"
            >

            <div class="author-info">

                <h5 class="author-name">
                    @${author.login} · ${jobs[author.login]}
                </h5>

                <a 
                    href="${author.html_url}" 
                    target="_blank"
                    class="author-github"
                >
                    GitHub
                </a>

            </div>

        </li>            
        `;
        $("#author-list").append(authorItem);
    });
    let ctbrs = {
        "🌙 moon" : "assets/avatars/guer.jpg",
        "箐川" : "assets/avatars/pxy.jpg"
    }
    for (let name in ctbrs) {
        let authorItem = `
            <li class="author-item">

            <img 
                src="${ctbrs[name]}" 
                class="rounded-circle"
                width=60
                height=60
                alt="${name}"
            >

            <div class="author-info">

                <h5 class="author-name">
                    @${name} · ${jobs[name]}
                </h5>

            </div>

        </li>            
        `;
        $("#author-list").append(authorItem);
    }

    }).catch((_) => {
        let authorItem = `
        拉取作者信息失败`
        $("#author-list").append(authorItem);
    })
    loadCardInfo()
})
