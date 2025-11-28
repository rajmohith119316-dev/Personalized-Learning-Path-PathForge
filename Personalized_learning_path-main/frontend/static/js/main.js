(function(){
	const overlay = document.getElementById('loadingOverlay');
	const toastContainer = document.getElementById('toastContainer');
	
	window.showLoading = function(){
		if(overlay){ overlay.classList.remove('hidden'); }
	};
	
	window.hideLoading = function(){
		if(overlay){ overlay.classList.add('hidden'); }
	};
	
	window.showToast = function(message, type){
		if(!toastContainer) return;
		const toast = document.createElement('div');
		toast.className = `toast ${type || 'info'}`;
		toast.textContent = message;
		toastContainer.appendChild(toast);
		setTimeout(()=>{ toast.classList.add('show'); }, 10);
		setTimeout(()=>{
			toast.classList.remove('show');
			setTimeout(()=> toast.remove(), 300);
		}, 3000);
	};
})();
