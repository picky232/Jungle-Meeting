function openmenu() {
    document.querySelector('.infomenu').classList.toggle('open')
}
var arrow = document.getElementById('arrow-down')
arrow.addEventListener('click', () => {
    arrow.classList.toggle('rotate-180')
})

function rewriteInfo()
{
    $.ajax({
        type:`GET`,
        url: `/description`,
        success: function (response)
        {
            if(response["result"] !== "success")
            {
                alert("다시 로그인 해주세요.");
                window.location.href = `/`;
            }
        }
    })
}