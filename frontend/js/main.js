let socket = null;
let reconnectTimer = null;
let reconnectAttempts = 0;
let manualSocketClose = false;

let fallbackClientId = null;
function getClientId() {
    try {
        // 每个标签页独立保存连接 ID；localStorage 会让两个标签页
        // 共用同一个 ID，互相把对方的 WebSocket 顶掉。
        let id = sessionStorage.getItem("woc_client_id");
        if (!id) {
            id = (window.crypto && window.crypto.randomUUID)
                ? window.crypto.randomUUID()
                : `woc-${Date.now()}-${Math.random().toString(16).slice(2)}`;
            sessionStorage.setItem("woc_client_id", id);
        }
        return id;
    } catch (_) {
        if (fallbackClientId === null) {
            fallbackClientId = `woc-${Date.now()}-${Math.random().toString(16).slice(2)}`;
        }
        return fallbackClientId;
    }
}
const CLIENT_ID = getClientId();

function connectSocket() {
    if (socket && (socket.readyState === WebSocket.OPEN
            || socket.readyState === WebSocket.CONNECTING)) {
        return;
    }
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const current = new WebSocket(
        `${protocol}://${window.location.host}/ws?client_id=${encodeURIComponent(CLIENT_ID)}`
    );
    socket = current;
    current.onopen = () => {
        if (socket !== current) {
            return;
        }
        reconnectAttempts = 0;
        showNotice("已连接服务器", "success");
    };
    current.onmessage = handleSocketMessage;
    current.onclose = () => {
        if (socket !== current || manualSocketClose) {
            return;
        }
        scheduleReconnect();
    };
    current.onerror = () => {
        // onclose will handle the retry.
    };
}

function scheduleReconnect() {
    if (manualSocketClose || reconnectTimer !== null) {
        return;
    }
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000);
    reconnectAttempts += 1;
    showNotice("连接断开，正在尝试重连…", "warning");
    reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        connectSocket();
    }, delay);
}
function safeSocketSend(payload) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(payload);
    } else {
        showNotice("连接中，请稍候…", "warning");
    }
}
window.addEventListener("beforeunload", () => {
    manualSocketClose = true;
    if (socket) {
        socket.close();
    }
});
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
let gameOverTimer = null;
let gameOverPending = false;
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
    safeSocketSend(
        JSON.stringify({
            action: "create_room",
        })
    )
})

$("#join-room-button").click(() => {
    showJoinRoomUI();
    $("#join-room-id").focus();
})
$("#ai-room-button").click(() => {
    safeSocketSend(
        JSON.stringify({
            action: "create_room",
            vs_ai: true,
        })
    )
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
    safeSocketSend(
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
    safeSocketSend(
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
    safeSocketSend(JSON.stringify({
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
    safeSocketSend(JSON.stringify({
        action: "player_operation",
        op_type: "surrender"
    }));
    $(this)
        .prop("disabled", true)
        .text("已投降");
});
function handleSocketMessage(event) {
    let data = JSON.parse(event.data);
    console.log("Received message:", data);
    if (data.type === "ping") {
        if (socket && socket.readyState === WebSocket.OPEN) {
            safeSocketSend(JSON.stringify({ action: "pong" }));
        }
        return;
    }
    if (data.type === "reconnected") {
        showNotice("已重新连接", "success");
        if (data.in_game) {
            enterGame();
        } else if (data.room_id) {
            showRoomUI(data.room_id);
        }
        return;
    }
    if( data.type === "room_created" ) {
        let roomId = data.room_id;
        if (!data.vs_ai) {
            showRoomUI(roomId);
        }
    }
    if (data.type === "game_start") {
        showNotice("游戏已开始", "success");

        enterGame()
    }
    if (data.type === "opponent_disconnected") {
        showNotice(`对方掉线，等待重连…`, "warning");
    }
    if (data.type === "opponent_reconnected") {
        showNotice("对方已重新连接", "success");
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
    if (data.type === "unit_death") {
        showUnitDeaths(data.units)
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
    $("#unit-detail-tooltip").removeClass("active");
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
        let element = $(`
            <div class="battle-unit ${owner_class} ${action_class}" data-unit-id="${unit.id}" data-owner="${unit.owner}">
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
function createDeathGhost(unit) {
    let temp = $("<div></div>").appendTo("body");
    let unit_data = Object.assign({}, unit, {
        canMove: false,
        canAttack: false,
    });
    renderUnits([unit_data], temp, gameState.my_side);
    let ghost = temp.children(".battle-unit").first();
    temp.remove();
    return ghost;
}
function showUnitDeaths(units) {
    if (!Array.isArray(units) || !gameState) {
        return;
    }
    units.forEach((unit) => {
        if (!unit || unit.timeline !== gameState.cur_bf) {
            return;
        }
        let existing = $(`.battle-unit[data-unit-id="${unit.id}"]`);
        let ghost = createDeathGhost(unit);
        let left;
        let top;
        let width;
        let height;

        if (existing.length) {
            let rect = existing[0].getBoundingClientRect();
            left = rect.left;
            top = rect.top;
            width = rect.width;
            height = rect.height;
            // The real element will be removed by the following state update;
            // hide it so only the 1s ghost remains visible.
            existing.css("visibility", "hidden");
        } else {
            let rel = gameState.my_side === "A" ? unit.fl : 2 - unit.fl;
            let container = $([
                "#player-base-units",
                "#frontline-units",
                "#enemy-base-units",
            ][rel] || "#frontline-units");
            if (!container.length) {
                return;
            }
            let rect = container[0].getBoundingClientRect();
            width = 120;
            height = 160;
            left = rect.left + rect.width / 2 - width / 2;
            top = rect.top + rect.height / 2 - height / 2;
        }

        if (!ghost || !ghost.length) {
            return;
        }
        ghost
            .removeAttr("data-unit-id")
            .removeClass("selected targetable attack-source attack-target")
            .addClass("unit-dying")
            .css({
                position: "fixed",
                left: `${left}px`,
                top: `${top}px`,
                width: `${width}px`,
                height: `${height}px`,
                margin: 0,
                zIndex: 4500,
                pointerEvents: "none",
            });
        $("body").append(ghost);
        setTimeout(() => ghost.remove(), 1000);
    });
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
    if (gameOverTimer !== null) {
        clearTimeout(gameOverTimer);
        gameOverTimer = null;
    }
    gameOverPending = false;
    $("#menu").addClass("hidden");
    $("#room-modal").removeClass("active");
    $("#game").removeClass("hidden");
    $("#ready-modal").removeClass("active");
    $("#game-over-modal").removeClass("active");
    $("#end-turn-button").prop("disabled", false);
    $("#surrender-button")
        .prop("disabled", false)
        .text("投降");
}
function displayGameOver(data) {
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
function showGameOver(data) {
    if (gameOverPending) {
        return;
    }
    gameOverPending = true;
    if (deployState.active) {
        cancelDeploy();
    }
    resetBattleInteractions();
    $("#hand-overlay").removeClass("active");
    $("#end-turn-button, #surrender-button").prop("disabled", true);

    // 投降立即结算；总部被击毁时先让玩家看到最后2.5秒的战场。
    if (data.reason === "surrender") {
        displayGameOver(data);
        return;
    }
    gameOverTimer = setTimeout(() => {
        gameOverTimer = null;
        displayGameOver(data);
    }, 2500);
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
    "Midsummer": "测试员",
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
    loadCardInfo().finally(() => {
        connectSocket()
    })
})
