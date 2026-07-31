let noticeTimer= null;
function showNotice(
    message,
    type="normal"
){
    if( noticeTimer ) {
        clearTimeout(noticeTimer)
        $(".wc-notice").remove();
    }
    let notice = $(`
    
    <div class="
        wc-notice
        ${type}
    ">
    ⚠ ${message}

    </div>

    `);
    $("#notice-container")
        .append(notice);
    noticeTimer = setTimeout(()=>{
        notice.addClass(
            "notice-hide"
        );
        setTimeout(()=>{
            notice.remove();
        },250);
    },2000);
}
function showBattleMessage(text, time=2000){
    $(".message-bar").text(text);
    $("#battle-message").removeClass("hidden");
    setTimeout(()=>{
        $("#battle-message").addClass("hidden");
    },time);
}