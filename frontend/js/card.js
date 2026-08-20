let cardInfo = [];
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
    cards.forEach(cardState=>{
        const info=getCardInfo(
            cardState.id
        );
        console.log("card state:", cardState);
        console.log("card info:", info);
        let element = ""
        if(info.type === "unit"){
            element=$(`  
            <div class="expanded-card">
                <div class="card-cost">
                    ${cardState.cost}
                </div>
                <div class="card-name">
                    ${info.name}
                </div>
                <div class="card-image">
                    <img src="assets/cards/${cardState.id}.jpg">
                </div>
                <div class="card-stats">
                    <span class="attack">
                        ${info.attack}
                    </span>
                    <span class="hp">
                        ${info.defense}
                    </span>
                </div>
                <div class="card-text">
                    ${info.effect}
                </div>
            </div>
            `);
        } else {
            element=$(`
            <div class="expanded-card">
                <div class="card-cost">
                    ${cardState.cost}
                </div>
                <div class="card-name">
                    ${info.name}
                </div>
                <div class="card-image">
                    <img src="assets/cards/${cardState.id}.jpg">
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

$(document).on("click", ".expanded-card", function(e){
    console.log("click card");
    e.stopPropagation();
    let card = $(this);
    // 已经选中
    if(card.hasClass("selected")){
        //取消部署状态
        card.removeClass("selected");
        setTimeout(()=>{
            $(".expanded-card")
                .removeClass("hidden");
        },0);
        $("#hand-overlay")
            .removeClass("deploy-mode");
        return;
    }
    // 第一次点击
    $(".expanded-card")
        .not(card)
        .addClass("hidden");
    card.addClass("selected");
    $("#hand-overlay")
        .addClass("deploy-mode");
})