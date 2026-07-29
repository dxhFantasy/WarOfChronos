function showRoomUI(roomId) {
    $("#room-id").text(roomId);

    $("#room-modal").addClass("active");
}
function hideRoomUI() {
    $("#room-modal").removeClass("active");
}
function showJoinRoomUI() {
    $("#join-room-modal").addClass("active");
}
function hideJoinRoomUI() {
    $("#join-room-modal").removeClass("active");
}
function showExitRoomUI() {
    $("#exit-game-modal").addClass("active");
}
function hideExitRoomUI() {
    $("#exit-game-modal").removeClass("active");
}
function showReadyCheckUI() {
    $("#ready-modal").addClass("active");
}
function hideReadyCheckUI() {
    $("#ready-modal").removeClass("active");
}
$("#room-id").click(() => {
    let id = $("#room-id").text();
    navigator.clipboard.writeText(id).then(() => {
        showNotice("房间号已复制到剪贴板", "success");
    });
});
$("#ready-button").click(() => {

    socket.send(JSON.stringify({

        type:"ready"

    }));


    $(this)
        .prop("disabled",true)
        .text("已准备");

});