let socket = new WebSocket(
    `ws://${window.location.host}/ws`
);
const authorList = ["dxhFantasy", "lwjyreq"]
let authorCache = new Array();
let deployState = {
    active : false,
    card_index : -1,
    card_element : null,
    target_kind : null,
    time_warp : false,
    prepared : false,
    pending_zone : null,
    command_timeline : null,
}
let handcards = []
let gameState = null;
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
    deployState.target_kind = null;
    deployState.time_warp = false;
    deployState.prepared = false;
    deployState.pending_zone = null;
    deployState.command_timeline = null;

    $(".expanded-card")
        .removeClass("selected")
        .removeClass("hidden");

    $(".deployable")
        .removeClass("deployable");

    cancelCommandTarget();
    hideTimelineSelect();

    $("#hand-overlay")
        .removeClass("deploy-mode");

    $("#close-hand")
        .removeClass("hidden");

    $("#end-turn-button")
        .removeClass("hidden");

    $("#use-command-button")
        .addClass("hidden")
        .css({
            left:"",
            top:"",
            transform:""
        });
    console.log("取消部署");
}
function enterDeploy(card_element) {
    deployState.active = true;
    deployState.card_element = card_element;
    deployState.card_index =
        Number(card_element.attr("data-index"));
    let card_state = handcards[deployState.card_index];
    deployState.target_kind = card_state.target || null;
    deployState.time_warp = !!card_state.timeWarp;
    deployState.prepared = !!card_state.prepared
        || (card_state.tags || []).includes("预备");
    deployState.pending_zone = null;
    deployState.command_timeline = null;
    cancelUnitSelection();
    console.log(card_element.attr("data-index"))
    $(".expanded-card")
        .not(card_element)
        .addClass("hidden");
    card_element.addClass("selected");
    $("#hand-overlay")
        .addClass("deploy-mode");
    $("#close-hand")
        .addClass("hidden");
    $("#end-turn-button")
        .addClass("hidden");
    console.log(91781369,cardInfo[handcards[deployState.card_index].id].type)
    if (cardInfo[handcards[deployState.card_index].id].type === "command") {
        updateCardButtonPosition(card_element)
        $("#use-command-button").removeClass("hidden")
    } else {
        $("#player-base-units")
            .addClass("deployable");
        if (deployState.prepared && (deployState.time_warp || frontlineAllowsDeploy())) {
            $("#frontline-units")
                .addClass("deployable");
            showInteractionHint("预备单位：可部署到我方前线");
        }
    }
}
function updateCardButtonPosition(card){

    let rect = card[0].getBoundingClientRect();

    $("#use-command-button")
        .css({
            left: `${rect.right + 30}px`,
            top: `${rect.top + rect.height / 2}px`,
            transform:"translateY(-50%)"
        });

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
    handleZoneClick("base");
});
$(document).on("click", "#frontline-units", function() {
    console.log("点击了前线");
    handleZoneClick("frontline");
});
$(document).on("click", "#end-turn-button", function() {
    if (gameState && !gameState.my_turn) {
        return;
    }
    cancelUnitSelection();
    socket.send(JSON.stringify({
        action: "player_operation",
        op_type: "end_turn"
    }));
});
$("#surrender-button").click(function() {
    if (!gameState) {
        return;
    }
    if (!window.confirm("确定要投降吗？")) {
        return;
    }
    if (deployState.active) {
        cancelDeploy();
    }
    resetBattleInteractions();
    socket.send(JSON.stringify({
        action: "player_operation",
        op_type: "surrender"
    }));
    $(this)
        .prop("disabled", true)
        .text("已投降");
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
        resetBattleInteractions();
    }
    if (data.type === "show_message") {
        console.log(data)
        if(data.subtitle !== undefined) {
            showBattleMessage(data.message, data.subtitle)
        } else {
            showBattleMessage(data.message)
        }
    }
    if (data.type === "update_state") {
        updateGameState(data)
    }
    if (data.type === "enemy_use_card") {
        play_enemy_use_card(data.card_id)
    }
    if (data.type === "attack_animation") {
        playAttackAnimation(data)
    }
    if (data.type === "game_over") {
        showGameOver(data)
    }
}
$("#use-command-button").click(() => {
    handleUseCommand();
})
function renderUnits(units, container, my_side){
    console.log(units)
    container.empty()
    units.map((unit, unit_idx) => {
        let info = cardInfo[unit.cardId] || {
            name : "未知单位",
            effect : ""
        }
        let owner_class =
            unit.owner === my_side ? "owner-self" : "owner-enemy"
        let action_class = ""
        if (unit.owner === my_side) {
            action_class =
                (unit.canMove || unit.canAttack) ? "can-act" : "spent"
        }
        let tags = (unit.tags || []).join(" / ")
        let element = $(`
            <div class="battle-unit ${owner_class} ${action_class}" data-unit-id="${unit.id}" data-owner="${unit.owner}" title="${tags}">
                <div class="unit-action-cost unit-cost">
                    ${unit.actionCost}
                </div>
                <div class="unit-name">
                    ${info.name}
                </div>
                <div class="unit-image">
                    <img src="assets/cards/${unit.cardId}.png" onerror="this.onerror=null;this.src='assets/testcard.jpg'">
                </div>
                <div class="unit-stats">
                    <span class="attack">
                        ⚔${unit.atk}
                    </span>

                    <span class="hp">
                        🛡${unit.dfns}
                    </span>
                </div>

            </div>
        `)

        container.append(element)
    })
}
function renderBattlefield(cur_bf, stateData) {
    if (!stateData || !stateData.battlefields) {
        return;
    }
    let frontlines = stateData.battlefields[cur_bf].frontlines
    const containers = [
        $("#player-base-units"),
        $("#frontline-units"),
        $("#enemy-base-units"),
    ]
    containers.map((container, idx) => {
        renderUnits(frontlines[idx].targets, container, stateData.my_side);
    })
    let owner = frontlines[1].owner || "N";
    let owner_label = "前线：中立";
    let owner_class = "owner-neutral";
    if (owner === stateData.my_side) {
        owner_label = "前线：我方占领";
        owner_class = "owner-self";
    } else if (owner === "A" || owner === "B") {
        owner_label = "前线：敌方占领";
        owner_class = "owner-enemy";
    } else if (owner === "X") {
        owner_label = "前线：争夺中";
        owner_class = "owner-contested";
    }
    $("#frontline-owner")
        .text(owner_label)
        .removeClass("owner-self owner-enemy owner-contested owner-neutral")
        .addClass(owner_class);
}
function updateGameState(stateData) {
    if(deployState.active){
        cancelDeploy();
    }
    resetBattleInteractions();
    gameState = stateData;

    console.log("Updating game state:", stateData);
    handcards = stateData.my_handcards;
    $("#my-act-point").text(`行动点: ${stateData.my_act_point}/${stateData.my_ap_slot}`);
    $("#enemy-act-point").text(`行动点: ${stateData.enemy_act_point}/${stateData.enemy_ap_slot}`);
    $("#my-hq-hp").text(`HP: ${stateData.my_hq}${stateData.my_hq_guarded ? " · 守护" : ""}`);
    $("#enemy-hq-hp").text(`HP: ${stateData.enemy_hq}${stateData.enemy_hq_guarded ? " · 守护" : ""}`);
    $("#player-hq")
        .toggleClass("guarded", !!stateData.my_hq_guarded)
        .attr("title", stateData.my_hq_guarded ? "我方总部被底线守护单位保护" : "");
    $("#enemy-hq")
        .toggleClass("guarded", !!stateData.enemy_hq_guarded)
        .attr("title", stateData.enemy_hq_guarded ? "敌方总部被底线守护单位保护" : "");
    $("#my-deck-counts").text(`${stateData.my_deck_cnts}`)
    $("#enemy-deck-counts").text(`${stateData.enemy_deck_counts}`)
    renderActionPointSlots(stateData.my_act_point, stateData.my_ap_slot, "#my-ap-slots");
    renderActionPointSlots(stateData.enemy_act_point, stateData.enemy_ap_slot, "#enemy-ap-slots");
    renderTurnInfo(stateData);
    renderTimeline(stateData.cur_bf);
    renderEvents(stateData.events, stateData.cur_bf);
    renderCompactHand(stateData.my_handcards);
    renderExpandedHand(stateData.my_handcards);
    renderEnemyHand(stateData.enemy_hc_counts);
    renderBattlefield(stateData.cur_bf, stateData);
}
function enterGame() {
    $("#menu").addClass("hidden");
    $("#room-modal").removeClass("active");
    $("#game").removeClass("hidden");
    $("#ready-modal").removeClass("active");
    $("#game-over-modal").removeClass("active");
    $("#surrender-button")
        .prop("disabled", false)
        .text("投降");
}
function showGameOver(data) {
    if (deployState.active) {
        cancelDeploy();
    }
    resetBattleInteractions();
    $("#hand-overlay").removeClass("active");
    let result = data.my_result || "draw";
    let title = "平局";
    if (result === "win") {
        title = "胜利";
    } else if (result === "lose") {
        title = "失败";
    }
    $("#game-over-title")
        .text(title)
        .removeClass("game-over-win game-over-lose game-over-draw")
        .addClass(`game-over-${result}`);
    $("#game-over-result").text(data.message || "战斗结束");
    $("#game-over-modal").addClass("active");
}
$("#game-over-return-button").click(() => {
    $("#game-over-modal").removeClass("active");
    $("#game").addClass("hidden");
    $("#menu").removeClass("hidden");
    gameState = null;
});

const jobs = {
    "dxhFantasy": "主策划/游戏设计",
    "lwjyreq": "前端网页/联机功能",
    "🌙 moon": "美术设计",
    "箐川" : "卡牌设计",
    "庆之" : "卡牌设计",
    "Midsummer": "忠实用户",
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
        "箐川" : "assets/avatars/pxy.jpg",
        "庆之" : "assets/avatars/lrz.jpg",
        "Midsummer": "assets/avatars/lzj.jpg"
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
