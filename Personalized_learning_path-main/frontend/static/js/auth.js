(function(){
    const USERS_KEY = 'users';
    const CURRENT_USER_LS = 'currentUser';
    const CURRENT_USER_SS = 'currentUserSession';

    function getUsers(){
        try { return JSON.parse(localStorage.getItem(USERS_KEY) || '[]'); } catch(_) { return []; }
    }
    function setUsers(users){ localStorage.setItem(USERS_KEY, JSON.stringify(users)); }

    function setCurrentUser(user, remember){
        const data = JSON.stringify(user);
        if(remember){
            localStorage.setItem(CURRENT_USER_LS, data);
            sessionStorage.removeItem(CURRENT_USER_SS);
        } else {
            sessionStorage.setItem(CURRENT_USER_SS, data);
            localStorage.removeItem(CURRENT_USER_LS);
        }
    }
    function clearCurrentUser(){
        localStorage.removeItem(CURRENT_USER_LS);
        sessionStorage.removeItem(CURRENT_USER_SS);
    }
    function getCurrentUser(){
        try {
            return JSON.parse(sessionStorage.getItem(CURRENT_USER_SS) || localStorage.getItem(CURRENT_USER_LS) || 'null');
        } catch(_) { return null; }
    }

    // Validation helpers
    function isValidEmail(email){
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(String(email).toLowerCase());
    }
    function isStrongPassword(pw){
        return /[A-Z]/.test(pw) && /[0-9]/.test(pw) && pw.length >= 8;
    }

    // Sign up
    async function signUp({ name, email, password, confirmPassword }){
        if(!name || name.trim().length < 2) throw new Error('Please enter your full name');
        if(!isValidEmail(email)) throw new Error('Please enter a valid email');
        if(!isStrongPassword(password)) throw new Error('Password must be 8+ chars, include uppercase and number');
        if(password !== confirmPassword) throw new Error('Passwords do not match');

        const users = getUsers();
        if(users.some(u => u.email.toLowerCase() === email.toLowerCase())){
            throw new Error('An account with this email already exists');
        }
        const user = {
            id: Date.now(),
            name: name.trim(),
            email: email.trim().toLowerCase(),
            password: btoa(password),
            createdAt: new Date().toISOString()
        };
        users.push(user);
        setUsers(users);
        return { id: user.id, name: user.name, email: user.email };
    }

    // Sign in
    async function signIn({ email, password, remember }){
        if(!isValidEmail(email)) throw new Error('Enter a valid email');
        const users = getUsers();
        const user = users.find(u => u.email === email.trim().toLowerCase());
        if(!user) throw new Error('No account found with this email');
        if(user.password !== btoa(password)) throw new Error('Incorrect password');
        setCurrentUser({ id: user.id, name: user.name, email: user.email }, Boolean(remember));
        return { id: user.id, name: user.name, email: user.email };
    }

    async function logout(){ clearCurrentUser(); }

    function isAuthenticated(){ return Boolean(getCurrentUser()); }

    function requireAuth(redirectTo){
        if(!isAuthenticated()){
            window.location.href = redirectTo || '/login';
            return false;
        }
        return true;
    }

    // Inject logout button if authenticated
    document.addEventListener('DOMContentLoaded', function(){
        const body = document.body;
        body.classList.add('fade-in');
        // page transitions
        document.querySelectorAll('a[href], button[onclick]').forEach(el => {
            el.addEventListener('click', function(e){
                const href = el.getAttribute('href');
                if(href && href.startsWith('/')){
                    e.preventDefault();
                    body.classList.add('fade-out');
                    setTimeout(()=>{ window.location.href = href; }, 180);
                }
            });
        });

        if(isAuthenticated()){
            if(!document.getElementById('logoutBtnInjected')){
                const btn = document.createElement('button');
                btn.id = 'logoutBtnInjected';
                btn.className = 'btn btn-secondary';
                btn.style.position = 'fixed';
                btn.style.top = '12px';
                btn.style.right = '12px';
                btn.textContent = 'Logout';
                btn.onclick = async ()=>{
                    showConfirm('Are you sure you want to logout? Unsaved progress will be lost.', async ()=>{
                        await logout(); showToast('Logged out','info'); window.location.href = '/login';
                    });
                };
                document.body.appendChild(btn);
            }
        }
    });

    // Expose API
    window.auth = {
        getUsers, setUsers,
        getCurrentUser, setCurrentUser, clearCurrentUser,
        isValidEmail, isStrongPassword,
        signUp, signIn, logout, isAuthenticated, requireAuth
    };

    // Simple confirm modal
    window.showConfirm = function(message, onOk){
        const modal = document.getElementById('confirmModal');
        if(!modal) { if(confirm(message)) onOk&&onOk(); return; }
        document.getElementById('confirmTitle').textContent = 'Confirm';
        document.getElementById('confirmMessage').textContent = message;
        const ok = document.getElementById('confirmOk');
        ok.onclick = ()=>{ hideConfirm(); onOk&&onOk(); };
        modal.classList.add('show');
        modal.style.display='flex';
    };
    window.hideConfirm = function(){
        const modal = document.getElementById('confirmModal');
        if(modal){ modal.classList.remove('show'); modal.style.display='none'; }
    };
})();


