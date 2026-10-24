let cardInfo = [];
const CARD_TIMELINE_LABELS = ["A", "B", "C"];
const CARD_TIMELINE_NAMES = ["1990前", "1991-2050", "2050后"];
function renderCardTimelines(timelines) {
    return (timelines || []).map((timeline) => {
        let label = CARD_TIMELINE_LABELS[timeline] || "?";
        let name = CARD_TIMELINE_NAMES[timeline] || "未知时间线";
        return `<span class="card-timeline timeline-${timeline}" title="${name}">${label}</span>`;
    }).join("");
}
async function loadCardInfo(){
    const response = await fetch(
        "static/js/card_info.json"
    );
    cardInfo = await response.json();
}
function getCardInfo(id){
    console.log("cardInfo:", cardInfo);
    return cardInfo[id];
}
function renderCompactHand(cards){
    let gap = Math.min(
        35,
        280 / cards.length
    );
    $("#player-hand").empty();
    cards.forEach((card,index)=>{
        let div=$("<div>");
        div.addClass(
            "compact-card"
        );
        div.css({
            left:
            index * gap,
            zIndex:index
        });
        $("#player-hand")
            .append(div);
    });
}
/*
    @param card_counts: 敌方手牌数量
*/
function renderEnemyHand(card_counts){
    let gap = Math.min(
        35,
        280 / card_counts
    );
    $("#enemy-hand").empty();
    for(let i = 0; i < card_counts; i++){
        let div=$("<div>");
        div.addClass(
            "compact-card"
        );
        div.css({
            left:
            i * gap,
            zIndex:i
        });
        $("#enemy-hand")
            .append(div);
    };
}
function renderExpandedHand(cards) {
    const container = $("#expanded-hand");
    container.empty();
    cards.forEach((cardState,index)=>{
        const info=getCardInfo(
            cardState.id
        );
        console.log("card state:", cardState);
        console.log("card info:", info);
        let element = ""
        if(info.type === "unit"){
            element=$(`  
            <div class="expanded-card" data-index="${index}">
                <div class="card-cost">
                    ${cardState.cost}
                </div>
                <div class="card-name">
                    ${info.name}
                </div>
                <div class="card-timelines" title="所属时间线">
                    ${renderCardTimelines(cardState.timelines)}
                </div>
                <div class="card-tags">
                    ${(cardState.tags || []).map((tag) => `<span class="card-tag">${tag}</span>`).join("")}
                </div>
                <div class="card-image">
                    <img src="assets/cards/${cardState.id}.jpg" onerror="this.src='assets/testcard.jpg'">
                </div>
                <div class="card-stats">
                    <span class="attack">
                        ⚔${info.attack}
                    </span>
                    <span class="hp">
                        🛡${info.defense}
                    </span>
                </div>
                <div class="card-text">
                    ${info.effect}
                </div>
            </div>
            `);
        } else {
            element=$(`
            <div class="expanded-card" data-index="${index}">
                <div class="card-cost">
                    ${cardState.cost}
                </div>
                <div class="card-name">
                    ${info.name}
                </div>
                <div class="card-timelines" title="所属时间线">
                    ${renderCardTimelines(cardState.timelines)}
                </div>
                <div class="card-tags">
                    ${(cardState.tags || []).map((tag) => `<span class="card-tag">${tag}</span>`).join("")}
                </div>
                <div class="card-image">
                    <img src="assets/cards/${cardState.id}.jpg" onerror="this.src='assets/testcard.jpg'">
                </div>
                <div class="card-text">
                    ${info.effect}
                </div>
            </div>
            `);
        }
        
        container.append(element);
    });
}
function play_enemy_use_card(card_id) {
    let info = cardInfo[card_id] || { name: "未知指令", cost: 0, effect: "" };
    let card = $(`
        <div class="expanded-card card-fly">
            <div class="card-cost">
                    ${info.cost}
                </div>
                <div class="card-name">
                    ${info.name}
                </div>
                <div class="card-image">
                    <img src="assets/cards/${card_id}.jpg" onerror="this.src='assets/testcard.jpg'">
                </div>
                <div class="card-text">
                    ${info.effect}
                </div>
            </div>
        </div>
    `);
    $("body").append(card);
    let start = $("#enemy-hand")[0]
        .getBoundingClientRect();
    let target = $("#frontline-units")[0]
        .getBoundingClientRect();
    card.css({
        left:start.left + start.width/2 - 75,
        top:start.top + start.height/2 - 112
    });
    card[0].offsetHeight;
    card.css({
        left:target.left + target.width/2 - 75,
        top:target.top + target.height/2 - 112,
        transform:"scale(1.15)"
    });
    setTimeout(()=>{
        card.addClass("fade-out");
    },1600);
    setTimeout(()=>{
        card.remove();
    },2200);
}