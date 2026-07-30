let socket = new WebSocket(
    `ws://${window.location.host}/ws`
);
const authorList = ["dxhFantasy", "lwjyreq"]
let authorCache = new Array();

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
socket.onmessage = (event) => {
    let data = JSON.parse(event.data);

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
    }
}

function enterGame() {
    $("#menu").addClass("hidden");
    $("#room-modal").removeClass("active");
    $("#game").removeClass("hidden");
    $("#ready-modal").removeClass("active");
}

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
                    @${author.login} · ${author.login == "dxhFantasy" ? "主策划/游戏设计" : "前端网页/联机功能"}
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
        })
    }).catch((_) => {
        let authorItem = `
        拉取作者信息失败`
        $("#author-list").append(authorItem);
    })
})
console.log(createCard(testCard))