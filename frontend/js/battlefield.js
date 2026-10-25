/*
 * 战场交互：行动点槽、历史事件、单位移动/攻击、穿梭与指向性指令
 * 依赖 main.js 里的 socket / deployState / handcards / gameState
 */

const TIMELINE_NAMES = ["1990前", "1991-2050", "2050后"];
const TIMELINE_LABELS = ["A", "B", "C"];
const EVENT_INFO = [
    {
        name: "大航海",
        timeline: 0,
        desc: "关闭：每回合失去 1 个行动点"
    },
    {
        name: "第二次世界大战",
        timeline: 0,
        desc: "关闭：A 时段所有单位 +2+2，之后时段所有单位 -1-1"
    },
    {
        name: "美苏冷战",
        timeline: 0,
        desc: "关闭：回合开始时若处于本时段及以后，额外获得 2 行动点；B 所有单位 -1-1"
    },
    {
        name: "第三次世界大战",
        timeline: 1,
        desc: "开启：B 时段友方单位 -1 行动花费；A 所有手牌 -2 花费；C 所有单位 -3-2"
    },
];

let unitActionState = {
    active : false,
    unit : null,
    element : null,
    mode : null,
};

let commandTargetState = {
    active : false,
    target : null,
};

function renderActionPointSlots(current, slot, selector) {
    current = Math.max(Number(current) || 0, 0);
    slot = Math.max(Number(slot) || 0, 0);
    let total = Math.max(current, slot);
    let html = "";
    for (let i = 0; i < total; i++) {
        html += `<span class="ap-slot ${i < current ? "filled" : "empty"}"></span>`;
    }
    $(selector).html(html);
}

function renderEvents(events, cur_bf) {
    const container = $("#event-list");
    container.empty();
    if (!events) {
        return;
    }
    EVENT_INFO.forEach((event, index) => {
        let opened = !!events[index];
        let item = $(`
            <div class="event-item ${opened ? "event-open" : "event-closed"} ${event.timeline === cur_bf ? "event-current" : ""}" title="${event.desc}">
                <span class="event-timeline">${TIMELINE_LABELS[event.timeline]}</span>
                <span class="event-name">${event.name}</span>
                <span class="event-state">${opened ? "开启" : "关闭"}</span>
            </div>
        `);
        container.append(item);
    });
}

function renderTimeline(cur_bf) {
    $("#timeline-name").text(`时间线: ${TIMELINE_NAMES[cur_bf] || "未知"}`);
}

function renderTurnInfo(stateData) {
    $("#my-turn-info").text(
        `第 ${stateData.total_turn} 回合 · ${stateData.my_turn ? "我方行动" : "对方行动"}`
    );
    $("#end-turn-button")
        .prop("disabled", !stateData.my_turn)
        .text(stateData.my_turn ? "结束回合" : "对方回合");
}

function showInteractionHint(text) {
    $("#interaction-hint")
        .text(text)
        .removeClass("hidden");
}

function hideInteractionHint() {
    $("#interaction-hint")
        .text("")
        .addClass("hidden");
}

function resetBattleInteractions() {
    cancelUnitSelection();
    cancelCommandTarget();
    hideTimelineSelect();
    hideInteractionHint();
}

function findUnitById(unit_id) {
    if (!gameState || !gameState.battlefields) {
        return null;
    }
    let bf = gameState.battlefields[gameState.cur_bf];
    if (!bf) {
        return null;
    }
    for (const frontline of bf.frontlines) {
        for (const unit of frontline.targets) {
            if (unit.id === unit_id) {
                return unit;
            }
        }
    }
    return null;
}

function findUnitElement(unit_id) {
    return $(`.battle-unit[data-unit-id="${unit_id}"]`);
}

function cancelUnitSelection() {
    unitActionState.active = false;
    unitActionState.unit = null;
    unitActionState.element = null;
    unitActionState.mode = null;
    $(".battle-unit").removeClass("selected targetable");
    $("#player-base-units, #frontline-units").removeClass("move-target");
    $("#enemy-hq, #player-hq").removeClass("targetable");
    $("#unit-actions").addClass("hidden");
    hideInteractionHint();
}

function selectUnit(unit, element) {
    cancelDeploy();
    cancelUnitSelection();
    unitActionState.active = true;
    unitActionState.unit = unit;
    unitActionState.element = element;
    element.addClass("selected");
    $("#unit-move-button")
        .toggleClass("hidden", !unit.canMove);
    $("#unit-attack-button")
        .toggleClass("hidden", !unit.canAttack);
    let rect = element[0].getBoundingClientRect();
    $("#unit-actions")
        .removeClass("hidden")
        .css({
            left: `${Math.min(Math.max(rect.left + rect.width / 2, 130), window.innerWidth - 130)}px`,
            top: `${Math.max(rect.top - 10, 70)}px`,
            transform: "translate(-50%,-100%)"
        });
}

function enterUnitMoveMode() {
    if (!unitActionState.active) {
        return;
    }
    unitActionState.mode = "move";
    $("#unit-actions").addClass("hidden");
    let unit = unitActionState.unit;
    if ((unit.moveTargets || []).includes("base")) {
        $("#player-base-units").addClass("move-target");
    }
    if ((unit.moveTargets || []).includes("frontline")) {
        $("#frontline-units").addClass("move-target");
    }
    showInteractionHint("请选择移动位置（点击发光区域）");
}

function enterUnitAttackMode() {
    if (!unitActionState.active) {
        return;
    }
    unitActionState.mode = "attack";
    $("#unit-actions").addClass("hidden");
    let unit = unitActionState.unit;
    let targets = unit.attackTargets || [];
    $(".battle-unit").each(function() {
        let id = Number($(this).attr("data-unit-id"));
        if (targets.includes(id)) {
            $(this).addClass("targetable");
        }
    });
    if (unit.canAttackHq) {
        $("#enemy-hq").addClass("targetable");
    }
    showInteractionHint("请选择攻击目标");
}

function sendUnitMove(zone) {
    let unit = unitActionState.unit;
    if (!unit) {
        return;
    }
    socket.send(JSON.stringify({
        action: "player_operation",
        op_type: "move_unit",
        unit_id: unit.id,
        target: zone
    }));
    cancelUnitSelection();
    $("#hand-overlay").removeClass("active");
}

function sendUnitAttack(target) {
    let unit = unitActionState.unit;
    if (!unit) {
        return;
    }
    let payload = {
        action: "player_operation",
        op_type: "attack_unit",
        unit_id: unit.id
    };
    if (target.target_hq) {
        payload.target_hq = true;
    } else {
        payload.target_id = target.target_id;
    }
    socket.send(JSON.stringify(payload));
    cancelUnitSelection();
    $("#hand-overlay").removeClass("active");
}

function handleUnitClick(element) {
    let unit_id = Number(element.attr("data-unit-id"));
    let unit = findUnitById(unit_id);
    if (!unit) {
        return false;
    }
    if (commandTargetState.active) {
        return pickCommandTargetUnit(unit);
    }
    if (deployState.active) {
        return false;
    }
    if (unitActionState.active && unitActionState.mode === "attack") {
        if ((unitActionState.unit.attackTargets || []).includes(unit.id)) {
            sendUnitAttack({ target_id : unit.id });
        }
        return true;
    }
    if (unitActionState.active && unitActionState.mode === "move") {
        return false;
    }
    if (!gameState || unit.owner !== gameState.my_side) {
        return false;
    }
    if (!gameState.my_turn) {
        showNotice("当前是对方回合", "warning");
        return true;
    }
    if (unitActionState.active && unitActionState.unit.id === unit.id) {
        cancelUnitSelection();
        return true;
    }
    if (!unit.canMove && !unit.canAttack) {
        showNotice("该单位本回合无法行动", "warning");
        return true;
    }
    selectUnit(unit, element);
    return true;
}

function handleHqClick(side) {
    if (commandTargetState.active && pickCommandTargetHq(side)) {
        return true;
    }
    if (unitActionState.active
        && unitActionState.mode === "attack"
        && side === "enemy"
        && unitActionState.unit.canAttackHq) {
        sendUnitAttack({ target_hq : true });
        return true;
    }
    return false;
}

function handleZoneClick(zone) {
    if (unitActionState.active && unitActionState.mode === "move") {
        let unit = unitActionState.unit;
        if ((unit.moveTargets || []).includes(zone)) {
            sendUnitMove(zone);
        }
        return;
    }
    if (!deployState.active) {
        return;
    }
    let card_state = handcards[deployState.card_index];
    if (!card_state) {
        return;
    }
    let info = cardInfo[card_state.id];
    if (!info || info.type !== "unit") {
        return;
    }
    if (zone === "frontline") {
        if (!deployState.prepared) {
            return;
        }
        if (!deployState.time_warp && !frontlineAllowsDeploy()) {
            showNotice("前线已被敌方占领或已经满员", "warning");
            return;
        }
    }
    if (deployState.time_warp) {
        // 穿梭单位：先确定部署位置，再选择要部署到的时间线
        deployState.pending_zone = zone;
        openTimelineSelect();
        return;
    }
    sendDeploy(zone, null);
}

function sendDeploy(zone, timeline) {
    let payload = {
        action: "player_operation",
        op_type: "deploy_unit",
        card_index: deployState.card_index,
        target: zone === "base" ? "player_base" : "frontline"
    };
    if (timeline !== null && timeline !== undefined) {
        payload.timeline = timeline;
    }
    socket.send(JSON.stringify(payload));
    $("#hand-overlay").removeClass("active");
    hideTimelineSelect();
    cancelDeploy();
}

function frontlineAllowsDeploy() {
    if (!gameState || !gameState.battlefields) {
        return false;
    }
    let bf = gameState.battlefields[gameState.cur_bf];
    if (!bf || !bf.frontlines || !bf.frontlines[1]) {
        return false;
    }
    let front = bf.frontlines[1];
    let owner_ok = !front.owner
        || front.owner === "N"
        || front.owner === gameState.my_side;
    return owner_ok && front.targets.length < front.maxTargets;
}

function handleUseCommand() {
    if (!deployState.active) {
        return;
    }
    if (deployState.time_warp) {
        openTimelineSelect();
        return;
    }
    if (deployState.target_kind) {
        enterCommandTarget();
        return;
    }
    sendUseCard(null);
}

function commandTargetSideMatches(owner, side) {
    if (side === "any") {
        return true;
    }
    if (!gameState) {
        return false;
    }
    if (side === "enemy") {
        return owner !== gameState.my_side;
    }
    return owner === gameState.my_side;
}

function commandTargetUnitValid(unit, side, zone) {
    if (zone === "hq") {
        return false;
    }
    return commandTargetSideMatches(unit.owner, side);
}

function enterCommandTarget() {
    let kind = deployState.target_kind || "";
    let parts = kind.split("_");
    let side = parts[0] || "any";
    let zone = parts[1] || "any";
    commandTargetState.active = true;
    commandTargetState.target = null;
    let count = 0;
    if (zone !== "hq") {
        $(".battle-unit").each(function() {
            let unit = findUnitById(Number($(this).attr("data-unit-id")));
            if (unit && commandTargetUnitValid(unit, side, zone)) {
                $(this).addClass("targetable");
                count += 1;
            }
        });
    }
    if (zone !== "unit") {
        if (side === "enemy" || side === "any") {
            $("#enemy-hq").addClass("targetable");
            count += 1;
        }
        if (side === "friendly" || side === "any") {
            $("#player-hq").addClass("targetable");
            count += 1;
        }
    }
    if (count === 0) {
        showNotice("没有可选择的合法目标", "warning");
        cancelDeploy();
        return;
    }
    $("#use-command-button").addClass("hidden");
    showInteractionHint("请选择指令目标");
}

function cancelCommandTarget() {
    commandTargetState.active = false;
    commandTargetState.target = null;
    $(".battle-unit").removeClass("targetable");
    $("#enemy-hq, #player-hq").removeClass("targetable");
    hideInteractionHint();
}

function pickCommandTargetUnit(unit) {
    if (!commandTargetState.active || !deployState.active) {
        return false;
    }
    let kind = deployState.target_kind || "";
    let parts = kind.split("_");
    let side = parts[0] || "any";
    let zone = parts[1] || "any";
    if (!commandTargetUnitValid(unit, side, zone)) {
        return false;
    }
    commandTargetState.target = { target_id : unit.id };
    afterCommandTargetPicked();
    return true;
}

function pickCommandTargetHq(side) {
    if (!commandTargetState.active || !deployState.active) {
        return false;
    }
    let kind = deployState.target_kind || "";
    let parts = kind.split("_");
    let target_side = parts[0] || "any";
    let zone = parts[1] || "any";
    if (zone === "unit") {
        return false;
    }
    if (side === "enemy" && target_side === "friendly") {
        return false;
    }
    if (side === "friendly" && target_side === "enemy") {
        return false;
    }
    commandTargetState.target = {
        target_hq : true,
        target_hq_side : side
    };
    afterCommandTargetPicked();
    return true;
}

function afterCommandTargetPicked() {
    if (deployState.command_timeline !== null) {
        sendUseCard(deployState.command_timeline);
        return;
    }
    if (deployState.time_warp) {
        openTimelineSelect();
        return;
    }
    sendUseCard(null);
}

function sendUseCard(timeline) {
    let card_index = deployState.card_index;
    let payload = {
        action: "player_operation",
        op_type: "use_card",
        card_index: card_index
    };
    if (commandTargetState.target) {
        Object.assign(payload, commandTargetState.target);
    }
    if (timeline !== null && timeline !== undefined) {
        payload.timeline = timeline;
    }
    socket.send(JSON.stringify(payload));
    hideTimelineSelect();
    cancelDeploy();
    $("#hand-overlay").removeClass("active");
}

function openTimelineSelect() {
    if (!deployState.active) {
        return;
    }
    if (!gameState) {
        return;
    }
    let isDeploy = !!deployState.pending_zone;
    $("#timeline-title").text(isDeploy ? "穿梭部署" : "穿梭");
    $("#timeline-hint").text(isDeploy
        ? "选择要部署到的时间线"
        : "选择要前往的时间线");
    let options = $("#timeline-options");
    options.empty();
    let enabled = 0;
    TIMELINE_NAMES.forEach((name, index) => {
        let button = $(`
            <button class="wc-button timeline-option" data-timeline="${index}">
                ${TIMELINE_LABELS[index]} · ${name}
                ${index === gameState.cur_bf ? "（当前）" : ""}
            </button>
        `);
        if (index === gameState.cur_bf) {
            button.prop("disabled", true);
        } else if (isDeploy && !timelineDeployAllowed(index)) {
            button.prop("disabled", true);
            button.attr("title", "该时间线没有可用的部署位置");
        } else {
            enabled += 1;
        }
        options.append(button);
    });
    if (isDeploy && enabled === 0) {
        showNotice("没有可部署的时间线", "warning");
    }
    $("#use-command-button").addClass("hidden");
    $("#timeline-modal").addClass("active");
}

function timelineDeployAllowed(index) {
    if (!gameState || !gameState.battlefields) {
        return false;
    }
    let bf = gameState.battlefields[index];
    if (!bf || !bf.frontlines) {
        return false;
    }
    let line_index = 1;
    if (deployState.pending_zone === "base") {
        line_index = gameState.my_side === "A" ? 0 : 2;
    }
    let line = bf.frontlines[line_index];
    if (!line) {
        return false;
    }
    if (line.targets.length >= line.maxTargets) {
        return false;
    }
    if (line_index === 1) {
        let owner_ok = !line.owner
            || line.owner === "N"
            || line.owner === gameState.my_side;
        if (!owner_ok) {
            return false;
        }
    }
    return true;
}

function confirmTimeline(timeline) {
    if (deployState.pending_zone) {
        let zone = deployState.pending_zone;
        deployState.pending_zone = null;
        sendDeploy(zone, timeline);
        return;
    }
    if (deployState.target_kind) {
        deployState.command_timeline = timeline;
        hideTimelineSelect();
        enterCommandTarget();
        return;
    }
    sendUseCard(timeline);
}

function hideTimelineSelect() {
    $("#timeline-modal").removeClass("active");
}

function playAttackAnimation(data) {
    if (!data || data.attacker_id === undefined) {
        return;
    }
    let attacker = $(`.battle-unit[data-unit-id="${data.attacker_id}"]`);
    let target;
    if (data.target_hq) {
        let my_side = gameState ? gameState.my_side : "A";
        target = data.target_hq_owner === my_side
            ? $("#player-hq")
            : $("#enemy-hq");
    } else {
        target = $(`.battle-unit[data-unit-id="${data.target_id}"]`);
    }
    if (!attacker.length || !target.length) {
        return;
    }
    let ar = attacker[0].getBoundingClientRect();
    let tr = target[0].getBoundingClientRect();
    let x1 = ar.left + ar.width / 2;
    let y1 = ar.top + ar.height / 2;
    let x2 = tr.left + tr.width / 2;
    let y2 = tr.top + tr.height / 2;
    let dx = x2 - x1;
    let dy = y2 - y1;
    let length = Math.hypot(dx, dy);
    let angle = Math.atan2(dy, dx) * 180 / Math.PI;
    let line = $("<div class='attack-line'></div>").css({
        left: `${x1}px`,
        top: `${y1 - 1}px`,
        width: `${length}px`,
        transform: `rotate(${angle}deg)`
    });
    $("body").append(line);
    attacker.addClass("attack-source");
    target.addClass("attack-target");
    setTimeout(() => {
        line.addClass("attack-line-fade");
    }, 380);
    setTimeout(() => {
        line.remove();
        attacker.removeClass("attack-source");
        target.removeClass("attack-target");
    }, 650);
}

$(document).on("click", ".battle-unit", function(e) {
    if (handleUnitClick($(this))) {
        e.stopPropagation();
    }
});
$(document).on("click", "#enemy-hq", function(e) {
    if (handleHqClick("enemy")) {
        e.stopPropagation();
    }
});
$(document).on("click", "#player-hq", function(e) {
    if (handleHqClick("friendly")) {
        e.stopPropagation();
    }
});
$("#unit-move-button").click(() => {
    enterUnitMoveMode();
});
$("#unit-attack-button").click(() => {
    enterUnitAttackMode();
});
$("#unit-cancel-button").click(() => {
    cancelUnitSelection();
});
$(document).on("click", ".timeline-option", function() {
    if ($(this).prop("disabled")) {
        return;
    }
    let timeline = Number($(this).attr("data-timeline"));
    if (Number.isNaN(timeline)) {
        return;
    }
    confirmTimeline(timeline);
});
$("#timeline-cancel-button").click(() => {
    hideTimelineSelect();
    cancelDeploy();
});
$(document).on("keydown", (e) => {
    if (e.key === "Escape") {
        if (deployState.active) {
            cancelDeploy();
            return;
        }
        cancelUnitSelection();
    }
});
