let socket = new WebSocket(
    `ws://${window.location.host}/ws`
);

$("#settings-button").click(() => {
    showNotice("敬请期待")
})

$("#start-room-button").click(() => {
    socket.send(
        JSON.stringify({
            action: "create_room",
        })
    )
})

$("#join-room-button").click(() => {
    showJoinRoomUI();
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
}

function enterGame() {
    $("#menu").addClass("hidden");
    $("#room-modal").removeClass("active");
    $("#game").removeClass("hidden");
}