const testCard = {
    cost : "3",
    type : "类型",
    name : "卡牌名",
    image : "assets/testcard2.jpg",
    attack: 3,
    hp : 10,
    effect : "效果"
}
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
                ♥ ${cardData.hp}
            </span>
        </div>
        <div class="card-keywords">
            ${cardData.effect}
        </div>
    </div>
    `;
}
