function createCard(cardData){
    return `
    <div class="card">
        <div class="card-cost">
            ${cardData.cost}
        </div>
        <div class="card-type">
            ${cardData.type}
        </div>
        <div class="card-name">
            ${cardData.name}
        </div>
        <div class="card-image">
            <img src="${cardData.image}">
        </div>
        <div class="card-stats">
            <span>
                ⚔ ${cardData.attack}
            </span>

            <span>
                ♥ ${cardData.defense}
            </span>
        </div>
        <div class="card-keywords">
            ${cardData.effect}
        </div>
    </div>
    `;
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
function renderExpandedHand(cards) {
    const container = $("#expanded-hand");
    container.empty();
    cards.forEach(card => {
        const cardElement = $(`
            <div class="expanded-card"
                 data-id="${card.id}">

                <img src="assets/cards/${card.id}.jpg">

                <div class="card-cost">
                    ${card.cost}
                </div>

            </div>
        `);
        container.append(cardElement);
    });
}