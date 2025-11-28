(function(){
	const token = localStorage.getItem('token');
	const authHeader = token ? { 'Authorization': 'Bearer ' + token } : {};
	let selectedRole = '';
	let skills = [];
	let currentStep = 1; // 1: career, 2: skills, 3: prefs
	let draft = null;
	let autosaveTimer = null;
	const MAX_SKILLS = 20;
	const DRAFT_KEY = 'learningPath_draft';

	function setProgress(){
		const fill = document.getElementById('progressFill');
		const text = document.getElementById('currentStep');
		const stepToShow = currentStep + 1;
		const pct = currentStep===1?40:(currentStep===2?60:80);
		if(fill){ fill.style.width = pct + '%'; }
		if(text){ text.textContent = stepToShow; }
	}

	function setStep(showSkills){
		const career = document.getElementById('stepCareer');
		const skillsStep = document.getElementById('stepSkills');
		const prefsStep = document.getElementById('stepPrefs');
		if(!career || !skillsStep) return;
		if(showSkills){
			career.style.display = 'none';
			skillsStep.style.display = '';
			if(prefsStep) prefsStep.style.display = 'none';
			currentStep = 2; setProgress();
		}else{
			career.style.display = '';
			skillsStep.style.display = 'none';
			if(prefsStep) prefsStep.style.display = 'none';
			currentStep = 1; setProgress();
		}
	}

	function setPrefsStep(){
		const career = document.getElementById('stepCareer');
		const skillsStep = document.getElementById('stepSkills');
		const prefsStep = document.getElementById('stepPrefs');
		if(!prefsStep) return;
		career.style.display = 'none';
		skillsStep.style.display = 'none';
		prefsStep.style.display = '';
		currentStep = 3; setProgress();
	}

	window.selectCareer = function(card){
		[...document.querySelectorAll('.career-card')].forEach(c=>c.classList.remove('selected'));
		card.classList.add('selected');
		selectedRole = card.getAttribute('data-role');
		const cont = document.getElementById('continueToSkillsBtn');
		const skipAll = document.getElementById('skipAllBtn');
		if(cont){ cont.disabled = !selectedRole; }
		if(skipAll){ skipAll.disabled = !selectedRole; }
		renderSuggestions();
		saveDraft();
	};

	window.goToSkills = function(){
		if(!selectedRole){ showToast('Select a career to continue','info'); return; }
		setStep(true);
		const input = document.getElementById('skillsInput');
		if(input){ input.focus(); }
	};

	window.backToCareer = function(){ setStep(false); };

	window.skipSkills = function(){ setPrefsStep(); };

	window.goToPrefs = function(){
		if(skills.length < 1){ showToast('Add at least one skill or press Skip','info'); return; }
		setPrefsStep();
		const dh = document.getElementById('dailyHours'); if(dh) dh.focus();
		saveDraft();
	};

	window.backToSkills = function(){ setStep(true); saveDraft(); };

	function normalizeSkill(s){ return s.trim().replace(/\s+/g,' '); }
	function existsSkill(s){
		const norm = s.toLowerCase();
		return skills.some(x => x.toLowerCase() === norm);
	}
	function addSkill(raw){
		const value = normalizeSkill(raw);
		if(!value) return;
		if(existsSkill(value)) { showToast('Skill already added','info'); return; }
		if(skills.length >= MAX_SKILLS){ showToast('You can add up to 20 skills','info'); return; }
		skills.push(value);
		renderChips();
		saveDraft();
	}
	function removeSkill(index){
		skills.splice(index,1);
		renderChips();
		saveDraft();
	}
	window.handleSkillInput = function(e){
		const keys = ['Enter', ','];
		if(keys.includes(e.key)){
			e.preventDefault();
			const input = e.target;
			const raw = input.value.replace(/,$/,'');
			addSkill(raw);
			input.value = '';
		}
	};

	function renderChips(){
		const container = document.getElementById('skillsChips');
		if(!container) return;
		container.innerHTML = '';
		skills.forEach((s, i) => {
			const chip = document.createElement('span');
			chip.className = 'chip';
			chip.textContent = s;
			const close = document.createElement('button');
			close.className = 'chip-remove';
			close.setAttribute('aria-label','Remove');
			close.innerHTML = '&times;';
			close.onclick = () => removeSkill(i);
			chip.appendChild(close);
			container.appendChild(chip);
			requestAnimationFrame(()=> chip.classList.add('show'));
		});
		const count = document.getElementById('skillsCountHint');
		if(count){ count.textContent = `${skills.length} skills added`; }
		const cont = document.getElementById('skillsContinueBtn');
		if(cont){ cont.disabled = skills.length < 1; }
	}

	const SUGGESTIONS = {
		'Full Stack Developer': ["HTML","CSS","JavaScript","React","Node.js","Git","REST APIs"],
		'Frontend Developer': ["HTML","CSS","JavaScript","React","Git","Responsive Design"],
		'Backend Developer': ["Python","REST APIs","SQL","Databases","Authentication","Git"],
		'Data Scientist': ["Python","Statistics","SQL","Pandas","NumPy","Machine Learning"],
		'UI/UX Designer': ["Figma","Adobe XD","Wireframing","Prototyping","User Research"],
		'DevOps Engineer': ["Linux","Docker","CI/CD","Cloud Platforms","Kubernetes","Monitoring"]
	};
	function renderSuggestions(){
		const wrap = document.getElementById('suggestedSkills');
		if(!wrap) return;
		wrap.innerHTML = '';
		(SUGGESTIONS[selectedRole]||[]).forEach((name)=>{
			const tag = document.createElement('span');
			tag.className = 'skill-tag';
			tag.textContent = name;
			tag.tabIndex = 0;
			tag.onclick = ()=> addSkill(name);
			tag.onkeydown = (e)=>{ if(e.key==='Enter' || e.key===','){ e.preventDefault(); addSkill(name);} };
			wrap.appendChild(tag);
		});
	}

	window.generatePath = async function(){
		if(!selectedRole){ showToast('Select a career to continue','info'); return; }
		const genBtn = document.getElementById('generateBtn');
		if(genBtn){ genBtn.classList.add('loading'); }
		showLoading();
		try{
			await fetch('/api/onboarding/goal',{
				method:'POST',
				headers:{'Content-Type':'application/json',...authHeader},
				body:JSON.stringify({goal:selectedRole, target_role:selectedRole})
			});
			// Save skills (optional; can be empty)
			await fetch('/api/onboarding/skills',{
				method:'POST',
				headers:{'Content-Type':'application/json',...authHeader},
				body:JSON.stringify({skills})
			});
			const prefs = gatherPreferences();
			await fetch('/api/onboarding/preferences',{
				method:'POST', headers:{'Content-Type':'application/json',...authHeader},
				body:JSON.stringify({ learning_pace:prefs.pace, daily_hours:prefs.daily_hours, preferred_content:prefs.preferred })
			});
			const res = await fetch('/api/ai/generate-path',{
				method:'POST',
				headers:{'Content-Type':'application/json',...authHeader}
			});
			const data = await res.json();
			if(res.ok){
				showToast('Learning path generated!','success');
				try{ localStorage.removeItem(DRAFT_KEY); }catch(_){ }
				setTimeout(()=>{ window.location.href = '/learning-path'; }, 500);
			}else{
				showToast(data.message||'Failed to generate','error');
			}
		} catch(e){
			showToast('Request failed','error');
		} finally { hideLoading(); if(genBtn){ genBtn.classList.remove('loading'); } }
	};

	function gatherPreferences(){
		const exp = (document.querySelector('input[name="exp"]:checked')||{}).value||'beginner';
		const pace = (document.querySelector('input[name="pace"]:checked')||{}).value||'moderate';
		const daily_hours = parseInt((document.getElementById('dailyHours')||{value:2}).value,10)||2;
		// Learning style section removed - using default content types
		const preferred = ['videos', 'articles', 'interactive'];
		return { exp, pace, daily_hours, preferred };
	}

	function saveDraft(){
		draft = { selectedCareer: selectedRole, knownSkills: skills, preferences: gatherPreferences(), timestamp: Date.now() };
		try{ localStorage.setItem(DRAFT_KEY, JSON.stringify(draft)); }catch(_){ }
	}

	function loadDraft(){
		try{
			const raw = localStorage.getItem(DRAFT_KEY);
			if(!raw) return;
			const d = JSON.parse(raw);
			if(!d || !d.timestamp) return;
			if(Date.now() - d.timestamp > 24*60*60*1000) return;
			if(confirm('Resume previous session?')){
				selectedRole = d.selectedCareer || '';
				skills = Array.isArray(d.knownSkills)? d.knownSkills : [];
				renderChips();
				if(selectedRole){
					[...document.querySelectorAll('.career-card')].forEach(c=>{ if(c.getAttribute('data-role')===selectedRole){ c.classList.add('selected'); }});
					renderSuggestions();
					const cont = document.getElementById('continueToSkillsBtn'); if(cont){ cont.disabled = false; }
					const skipAll = document.getElementById('skipAllBtn'); if(skipAll){ skipAll.disabled = false; }
				}
			}
		}catch(_){ }
	}

	function startAutosave(){ if(autosaveTimer) clearInterval(autosaveTimer); autosaveTimer = setInterval(saveDraft, 30000); }

	// Keyboard shortcuts
	document.addEventListener('keydown', (e)=>{
		if(e.key==='Escape'){
			if(currentStep===2) { window.backToCareer(); }
			else if(currentStep===3) { window.backToSkills(); }
		}
		if(e.key==='Enter'){
			if(currentStep===1){ const btn=document.getElementById('continueToSkillsBtn'); if(btn && !btn.disabled){ btn.click(); } }
			else if(currentStep===2){ const btn=document.getElementById('skillsContinueBtn'); if(btn && !btn.disabled){ btn.click(); } }
		}
	});

	setProgress();
	startAutosave();
	loadDraft();
})();
