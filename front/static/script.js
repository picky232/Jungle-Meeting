function openmenu() {
    document.querySelector('.infomenu').classList.toggle('open')
}
var arrow = document.getElementById('arrow-down')
arrow.addEventListener('click', () => {
    arrow.classList.toggle('rotate-180')
})

function rewriteInfo()
{
    window.location.href = `/description`;
}

function login()
{
    window.location.href = `/login`;
}

function signUp()
{
    window.location.href = `/signup`;
}

function logout()
{
    $.ajax({
        type:'GET',
        url:'/logout',
        success: function(response)
        {
            window.location.href = `/`;
        }
    })
}