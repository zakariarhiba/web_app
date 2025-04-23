var snd = new Audio('http://www.ilovewavs.com/Effects/Beeps/Click02.wav');
// delegated event on inputs of checkboxControl
document.addEventListener('change', function(e){
	if(e.target.parentNode.className.indexOf('checkboxControl') != -1){
		snd.currentTime = 0;
		snd.play(); 
	}
});
