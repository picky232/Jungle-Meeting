function openmenu(){
    document.querySelector('.infomenu').classList.toggle('open')
}
var arrow = document.getElementByid('arrow-down')
arrow.addEventListener('click', () => {
    arrow.classList.toggle('rotate-180')
})

