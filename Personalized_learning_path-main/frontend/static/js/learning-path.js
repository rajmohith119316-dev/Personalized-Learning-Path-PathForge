(async function(){
	const container = document.getElementById('pathContainer');
	function h(tag, cls, text){
		const el = document.createElement(tag);
		if(cls) el.className = cls;
		if(text) el.textContent = text;
		return el;
	}
	function renderPath(path){
		container.innerHTML = '';
		
		// Header section
		const header = h('div','path-header',null);
		header.appendChild(h('h2','',path.title || 'Learning Path'));
		if(path.description) {
			const desc = h('p','path-description',path.description);
			header.appendChild(desc);
		}
		container.appendChild(header);
		
		// Meta information
		const meta = h('div','path-meta',null);
		meta.textContent = `Estimated: ${path.estimated_duration_weeks||0} weeks • Difficulty: ${path.difficulty_level||'beginner'}`;
		container.appendChild(meta);
		
		// Modules section
		const modulesContainer = h('div','path-modules',null);
		(path.curriculum?.modules||[]).forEach((m, mi)=>{
			const card = h('div','feature-card path-module',null);
			
			// Module header
			const moduleHeader = h('div','module-header',null);
			moduleHeader.appendChild(h('h3','',`${mi+1}. ${m.title}`));
			if(m.estimated_hours || m.difficulty) {
				const moduleMeta = h('div','module-meta',null);
				moduleMeta.textContent = `~${m.estimated_hours||0} hrs${m.difficulty ? ' • ' + m.difficulty : ''}`;
				moduleHeader.appendChild(moduleMeta);
			}
			card.appendChild(moduleHeader);
			
			// Module description
			if(m.description) {
				const desc = h('p','module-description',m.description);
				card.appendChild(desc);
			}
			
			// Topics list
			if(m.topics && m.topics.length > 0) {
				const topicsTitle = h('h4','topics-title','Topics:');
				card.appendChild(topicsTitle);
				const list = h('ul','topics-list',null);
				m.topics.forEach(t=>{
					const li = h('li','topic-item',null);
					li.textContent = `${t.title}${t.estimated_hours ? ' (' + t.estimated_hours + 'h)' : ''}`;
				list.appendChild(li);
			});
			card.appendChild(list);
			}
			
			modulesContainer.appendChild(card);
		});
		container.appendChild(modulesContainer);
	}
	try{
		showLoading();
		const res = await fetch('/api/ai/path');
		const data = await res.json();
		if(res.ok && data.path){
			renderPath(data.path);
		}else{
			container.innerHTML = '<p>No path found. Please generate one first.</p>';
		}
	} catch(e){
		container.innerHTML = '<p>Failed to load learning path.</p>';
	} finally { hideLoading(); }
})();
