/**
 * main.js - SecureVote Client Application Logic
 * Course: CSE494 - Intelligent NoSQL Databases
 * Implements: Login-First Gateway, Voter Self-Registration & Approval Queue,
 * Admin Password Authentication (yeswanthburle1432@gmail.com), and Election Lifecycles.
 */

// =============================================================================
// GLOBAL APPLICATION STATE
// =============================================================================
let currentUser = {
    role: "guest",        // 'guest' | 'voter' | 'admin'
    is_admin: false,
    voter: null,
    admin_email: null
};

let currentVoterElectionId = null;
let currentAdminElectionId = null;
let activeElectionsList = [];
let allElectionsList = [];
let candidatesList = [];
let selectedCandidateId = null;
let selectedCandidateObj = null;
let lastReceiptData = null;
let adminCandidateVotesChart = null;
let adminDepartmentTurnoutChart = null;

// =============================================================================
// INITIALIZATION ON DOM READY
// =============================================================================
document.addEventListener("DOMContentLoaded", async () => {
    startSystemClock();
    await checkCurrentUserSession();
});

// =============================================================================
// SYSTEM CLOCK (Live UTC / System Time)
// =============================================================================
function startSystemClock() {
    const clockEl = document.getElementById("liveSystemClock");
    function updateClock() {
        if (!clockEl) return;
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const dateStr = now.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
        clockEl.textContent = `${dateStr} ${timeStr} • SECURE SYSTEM ACTIVE`;
    }
    updateClock();
    setInterval(updateClock, 1000);
}

// =============================================================================
// SESSION & ROLE-BASED ACCESS CONTROL
// =============================================================================
async function checkCurrentUserSession() {
    try {
        const res = await fetch("/api/auth/current-user");
        const data = await res.json();
        if (data.success && data.logged_in) {
            currentUser = {
                role: data.role || "guest",
                is_admin: data.is_admin || false,
                voter: data.voter || null,
                admin_email: data.admin_email || null
            };
        } else {
            currentUser = {
                role: "guest",
                is_admin: false,
                voter: null,
                admin_email: null
            };
        }
        applyStateToUI();
    } catch (e) {
        console.error("Session check error:", e);
        applyStateToUI();
    }
}

function applyStateToUI() {
    const viewGateway = document.getElementById("view-auth-gateway");
    const viewVoter = document.getElementById("view-voter-workspace");
    const viewAdmin = document.getElementById("view-admin-workspace");
    const header = document.getElementById("mainAppHeader");

    const voterNav = document.getElementById("voterNavGroup");
    const adminNav = document.getElementById("adminNavGroup");

    const userAvatar = document.getElementById("headerUserAvatar");
    const userName = document.getElementById("headerUserName");
    const userDesc = document.getElementById("headerUserDesc");
    const roleTag = document.getElementById("portalRoleTag");
    const subTitle = document.getElementById("portalSubTitle");

    // Hide all main containers
    if (viewGateway) viewGateway.classList.remove("active");
    if (viewVoter) viewVoter.classList.add("hidden");
    if (viewAdmin) viewAdmin.classList.add("hidden");
    if (header) header.classList.add("hidden");

    if (currentUser.role === "admin") {
        // ADMIN LOGGED IN
        if (header) header.classList.remove("hidden");
        if (viewAdmin) viewAdmin.classList.remove("hidden");
        if (adminNav) adminNav.classList.remove("hidden");
        if (voterNav) voterNav.classList.add("hidden");

        if (userAvatar) userAvatar.textContent = "🔐";
        if (userName) userName.textContent = "Admin";
        if (userDesc) userDesc.textContent = "Commission Administrator (Verified)";
        if (roleTag) roleTag.textContent = "ADMIN COMMISSION";
        if (subTitle) subTitle.textContent = "Full Electoral Governance & Candidate Management";

        switchAdminTab("queue");
        loadPendingVotersQueue();
        loadAdminElectionsTable();

    } else if (currentUser.role === "voter" && currentUser.voter) {
        // VOTER LOGGED IN
        const v = currentUser.voter;
        if (header) header.classList.remove("hidden");
        if (viewVoter) viewVoter.classList.remove("hidden");
        if (voterNav) voterNav.classList.remove("hidden");
        if (adminNav) adminNav.classList.add("hidden");

        const initials = v.name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
        if (userAvatar) userAvatar.textContent = initials;
        if (userName) userName.textContent = v.name;
        if (userDesc) userDesc.textContent = `${v.department} (${v.voter_id})`;
        if (roleTag) roleTag.textContent = "VOTER BOOTH";
        if (subTitle) subTitle.textContent = "Certified Anonymous Digital Ballot System";

        // Update Smart Card
        updateVoterSmartCard(v);
        switchVoterTab("voter-booth");
        loadVoterActiveElections();

    } else {
        // GUEST / UNICATED: SHOW ONLY AUTH GATEWAY!
        if (viewGateway) viewGateway.classList.add("active");
        selectAuthRole("voter");
    }
}

function updateVoterSmartCard(v) {
    const initials = v.name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
    const initialsEl = document.getElementById("voterCardInitials");
    const nameEl = document.getElementById("voterCardName");
    const idEl = document.getElementById("voterCardId");
    const deptEl = document.getElementById("voterCardDept");

    if (initialsEl) initialsEl.textContent = initials;
    if (nameEl) nameEl.textContent = v.name;
    if (idEl) idEl.textContent = v.voter_id;
    if (deptEl) deptEl.textContent = `${v.department} • Year ${v.year_of_study} (Age ${v.age})`;
}

async function triggerLogout() {
    try {
        await fetch("/api/auth/logout", { method: "POST" });
        currentUser = { role: "guest", is_admin: false, voter: null, admin_email: null };
        applyStateToUI();
        showToast("Signed out successfully. Authentication required to continue.", "info");
    } catch (e) {
        showToast("Logout error: " + e.message, "error");
    }
}

// =============================================================================
// AUTH GATEWAY UI INTERACTIONS
// =============================================================================
function selectAuthRole(role) {
    const btnVoter = document.getElementById("btnRoleTabVoter");
    const btnAdmin = document.getElementById("btnRoleTabAdmin");
    const panelVoter = document.getElementById("authPanelVoter");
    const panelAdmin = document.getElementById("authPanelAdmin");

    if (role === "admin") {
        if (btnAdmin) btnAdmin.classList.add("active");
        if (btnVoter) btnVoter.classList.remove("active");
        if (panelAdmin) panelAdmin.classList.remove("hidden");
        if (panelVoter) panelVoter.classList.add("hidden");
    } else {
        if (btnVoter) btnVoter.classList.add("active");
        if (btnAdmin) btnAdmin.classList.remove("active");
        if (panelVoter) panelVoter.classList.remove("hidden");
        if (panelAdmin) panelAdmin.classList.add("hidden");
    }
}

function toggleVoterMode(mode) {
    const btnLogin = document.getElementById("btnVoterSubtabLogin");
    const btnSignup = document.getElementById("btnVoterSubtabSignup");
    const formLogin = document.getElementById("voterLoginFormContainer");
    const formSignup = document.getElementById("voterSignupFormContainer");

    if (mode === "signup") {
        if (btnSignup) btnSignup.classList.add("active");
        if (btnLogin) btnLogin.classList.remove("active");
        if (formSignup) formSignup.classList.remove("hidden");
        if (formLogin) formLogin.classList.add("hidden");
    } else {
        if (btnLogin) btnLogin.classList.add("active");
        if (btnSignup) btnSignup.classList.remove("active");
        if (formLogin) formLogin.classList.remove("hidden");
        if (formSignup) formSignup.classList.add("hidden");
    }
}

// Voter Sign Up Form Submission
async function handleVoterSignup(e) {
    e.preventDefault();
    const btn = document.getElementById("btnSubmitVoterSignup");
    if (btn) btn.disabled = true;

    const nameEl = document.getElementById("regName");
    const emailEl = document.getElementById("regEmail");
    const passEl = document.getElementById("regPassword");
    const deptEl = document.getElementById("regDept");
    const yearEl = document.getElementById("regYear");
    const ageEl = document.getElementById("regAge");

    const payload = {
        name: nameEl ? nameEl.value.trim() : "",
        email: emailEl ? emailEl.value.trim().toLowerCase() : "",
        password: passEl ? passEl.value.trim() : "",
        department: deptEl ? deptEl.value : "Computer Science",
        year_of_study: yearEl ? parseInt(yearEl.value) : 1,
        age: ageEl ? parseInt(ageEl.value) : 18
    };

    try {
        const res = await fetch("/api/auth/voter-signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.success) {
            const assignedId = data.voter_id || "VTR-1001";
            showToast(`🎉 Registration submitted! Assigned Voter ID: ${assignedId}. Awaiting verification by the Admin.`, "success");
            toggleVoterMode("login");
            const loginInput = document.getElementById("voterLoginId");
            if (loginInput) loginInput.value = payload.email;
            const passInput = document.getElementById("voterLoginPass");
            if (passInput) {
                passInput.value = "";
                passInput.focus();
            }
        } else {
            showToast(data.error || "Signup failed.", "error");
        }
    } catch (err) {
        showToast("Error: " + err.message, "error");
    } finally {
        if (btn) btn.disabled = false;
    }
}

// Voter Login Form Submission
async function handleVoterLogin(e) {
    e.preventDefault();
    const btn = document.getElementById("btnSubmitVoterLogin");
    if (btn) btn.disabled = true;

    const identifier = document.getElementById("voterLoginId").value.trim();
    const password = document.getElementById("voterLoginPass").value.trim();

    try {
        const res = await fetch("/api/auth/voter-login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: identifier, voter_id: identifier, password: password })
        });
        const data = await res.json();

        if (data.success) {
            currentUser = { role: "voter", is_admin: false, voter: data.voter, admin_email: null };
            applyStateToUI();
            showToast(`Welcome back, ${data.voter.name}! Voting booth unlocked.`, "success");
        } else {
            if (data.is_pending) {
                showToast("Account Pending: Registration is awaiting verification by the Admin.", "warning");
            } else {
                showToast(data.error || "Login failed.", "error");
            }
        }
    } catch (err) {
        showToast("Login error: " + err.message, "error");
    } finally {
        if (btn) btn.disabled = false;
    }
}

// Admin Password Authentication (Permanent Password: Yash@1432)
async function handleAdminLogin(e) {
    if (e && e.preventDefault) e.preventDefault();
    const emailInput = document.getElementById("adminEmailInput");
    const passInput = document.getElementById("adminPasswordInput");
    const email = (emailInput ? emailInput.value : "").trim().toLowerCase();
    const password = (passInput ? passInput.value : "").trim();
    const btn = document.getElementById("btnAdminLogin");

    if (!password) {
        showToast("Please enter the administrator password.", "error");
        if (passInput) passInput.focus();
        return;
    }

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span>⏳ Authenticating Administrator...</span>`;
    }

    try {
        const res = await fetch("/api/auth/admin-login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: email, password: password })
        });
        const data = await res.json();

        if (data.success) {
            currentUser = { role: "admin", is_admin: true, voter: null, admin_email: data.admin_email };
            applyStateToUI();
            showToast("Welcome Administrator! Commission portal unlocked.", "success");
            if (passInput) passInput.value = "";
        } else {
            if (passInput) {
                passInput.classList.add("input-error");
                setTimeout(() => passInput.classList.remove("input-error"), 800);
            }
            showToast(data.error || "Authentication failed. Invalid password.", "error");
        }
    } catch (err) {
        showToast("Login error: " + err.message, "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<span>🔐 Sign In &amp; Unlock Commission Console</span> ➔`;
        }
    }
}

// Backward compatibility stubs
async function handleRequestAdminOtp(e) { return handleAdminLogin(e); }
async function handleVerifyAdminOtp(e) { return handleAdminLogin(e); }
async function resendAdminOtp() {}
function resetAdminOtpStep() {}

// =============================================================================
// VOTER PORTAL: BALLOT PAPER & VOTING WORKFLOW
// =============================================================================
function switchVoterTab(tabId) {
    const cleanKey = tabId.replace("voter-", "");
    
    // Hide all voter panes
    document.querySelectorAll(".voter-tab-pane").forEach(p => {
        p.classList.remove("active");
        p.classList.add("hidden");
    });
    // Remove active from all voter nav tabs
    document.querySelectorAll("#voterNavGroup .nav-tab").forEach(t => t.classList.remove("active"));

    // Activate target pane
    const targetPane = document.getElementById(`voter-tab-${cleanKey}`);
    if (targetPane) {
        targetPane.classList.remove("hidden");
        targetPane.classList.add("active");
    }

    const activeNav = document.querySelector(`#voterNavGroup .nav-tab[data-tab="${tabId}"]`);
    if (activeNav) activeNav.classList.add("active");

    if (cleanKey === "results") {
        loadVoterResults();
    } else if (cleanKey === "receipts") {
        loadVoterReceiptsHistory();
    } else if (cleanKey === "booth") {
        loadVoterBallot();
    }
}

async function loadVoterActiveElections() {
    try {
        // Fetch only elections that have status 'active' (accepted by admin)
        const res = await fetch("/api/elections?status=active");
        const data = await res.json();
        const select = document.getElementById("voterElectionSelect");

        if (data.success && data.elections && data.elections.length > 0) {
            activeElectionsList = data.elections;
            if (!currentVoterElectionId || !activeElectionsList.find(e => e.election_id === currentVoterElectionId)) {
                currentVoterElectionId = activeElectionsList[0].election_id;
            }

            if (select) {
                select.innerHTML = activeElectionsList.map(ele => `
                    <option value="${ele.election_id}" ${ele.election_id === currentVoterElectionId ? 'selected' : ''}>
                        ${escapeHtml(ele.title)}
                    </option>
                `).join("");
            }
            loadVoterBallot();
        } else {
            activeElectionsList = [];
            if (select) select.innerHTML = `<option value="">No Active Elections Opened by Admin</option>`;
            const grid = document.getElementById("voterCandidatesGrid");
            if (grid) {
                grid.innerHTML = `<div class="empty-state" style="padding: 2.5rem; text-align: center; color: var(--text-muted);">
                    No elections are currently open for voting. Please check back when the Admin opens an election.
                </div>`;
            }
        }
    } catch (e) {
        console.error("Error loading voter elections:", e);
    }
}

function onVoterElectionChange() {
    const select = document.getElementById("voterElectionSelect");
    if (!select) return;
    currentVoterElectionId = select.value;
    loadVoterBallot();
}

async function loadVoterBallot() {
    if (!currentUser.voter || !currentVoterElectionId) return;
    const voterId = currentUser.voter.voter_id;

    const titleEl = document.getElementById("voterElectionTitle");
    const descEl = document.getElementById("voterElectionDesc");
    const alreadyVotedNotice = document.getElementById("voterAlreadyVotedNotice");
    const electionClosedNotice = document.getElementById("voterElectionClosedNotice");
    const ballotPaperContainer = document.getElementById("ballotPaperContainer");
    const candidatesGrid = document.getElementById("voterCandidatesGrid");
    const btnCast = document.getElementById("btnCastBallot");
    const previewChoice = document.getElementById("voterSelectedChoiceText");

    // Reset selection state
    selectedCandidateId = null;
    selectedCandidateObj = null;
    if (previewChoice) previewChoice.textContent = "None Selected (Mark a candidate card)";
    if (btnCast) btnCast.disabled = true;

    const ele = activeElectionsList.find(e => e.election_id === currentVoterElectionId);
    if (ele) {
        if (titleEl) titleEl.textContent = ele.title;
        if (descEl) descEl.textContent = ele.description || "Review official candidates below and confirm your choice.";
    }

    try {
        // 1. Check voter's vote status for this election
        const statusRes = await fetch(`/api/voters/${encodeURIComponent(voterId)}/status?election_id=${encodeURIComponent(currentVoterElectionId)}`);
        const statusData = await statusRes.json();

        // 2. Fetch candidates for this election
        const candRes = await fetch(`/api/candidates?election_id=${encodeURIComponent(currentVoterElectionId)}`);
        const candData = await candRes.json();
        candidatesList = candData.candidates || [];

        if (statusData.has_voted) {
            // ALREADY VOTED: Show the clean voted card and hide the ballot container
            if (alreadyVotedNotice) {
                alreadyVotedNotice.classList.remove("hidden");
                const summary = document.getElementById("voterAlreadyVotedSummary");
                if (summary) {
                    summary.innerHTML = `
                        <div style="margin-top: 0.5rem;">Official Proof Token: <code style="color: var(--gold); font-weight: 700;">${statusData.receipt_token}</code></div>
                        <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">Timestamp: ${statusData.timestamp}</div>
                    `;
                }
            }
            if (ballotPaperContainer) ballotPaperContainer.classList.add("hidden");
            if (electionClosedNotice) electionClosedNotice.classList.add("hidden");
            lastReceiptData = {
                receipt_token: statusData.receipt_token,
                timestamp: statusData.timestamp,
                election_id: currentVoterElectionId,
                vote_id: "SEALED-GUID-" + voterId.slice(-4)
            };
        } else {
            // NOT VOTED: Check if election is active and display ballot paper
            if (alreadyVotedNotice) alreadyVotedNotice.classList.add("hidden");
            if (electionClosedNotice) electionClosedNotice.classList.add("hidden");
            if (ballotPaperContainer) ballotPaperContainer.classList.remove("hidden");
            renderVoterBallotCards(candidatesList, false);
        }
    } catch (e) {
        showToast("Error loading ballot: " + e.message, "error");
    }
}

function renderVoterBallotCards(candidates, isLocked) {
    const grid = document.getElementById("voterCandidatesGrid");
    if (!grid) return;

    if (!candidates || candidates.length === 0) {
        grid.innerHTML = `<div class="empty-state" style="padding: 2.5rem; text-align: center; color: var(--text-muted);">
            No candidate slates registered for this election yet.
        </div>`;
        return;
    }

    grid.innerHTML = candidates.map((cand, idx) => {
        const numStr = String(idx + 1).padStart(2, "0");
        const initials = cand.name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();

        return `
            <div class="candidate-ballot-card ${isLocked ? 'disabled' : ''}" id="voterCandCard_${cand.candidate_id}" onclick="${isLocked ? '' : `selectVoterCandidate('${cand.candidate_id}')`}">
                <div class="cand-top-row">
                    <div class="cand-avatar">${initials}</div>
                    <div class="cand-name-block">
                        <div class="cand-number">OFFICIAL BALLOT CHOICE #${numStr}</div>
                        <div class="cand-name">${escapeHtml(cand.name)}</div>
                        <div class="cand-party">${escapeHtml(cand.party_or_slate)}</div>
                        <div class="cand-dept">${escapeHtml(cand.department)}</div>
                    </div>
                </div>

                <div class="cand-manifesto-box">
                    "${escapeHtml(cand.manifesto || "Representing all students with dedication and transparency.")}"
                </div>

                <div class="ballot-selection-pill">
                    <span>${isLocked ? 'Ballot Cast' : 'Mark Candidate'}</span>
                </div>
            </div>
        `;
    }).join("");
}

function selectVoterCandidate(candidateId) {
    selectedCandidateId = candidateId;
    selectedCandidateObj = candidatesList.find(c => c.candidate_id === candidateId);

    document.querySelectorAll(".candidate-ballot-card").forEach(c => c.classList.remove("selected"));
    const activeCard = document.getElementById(`voterCandCard_${candidateId}`);
    if (activeCard) activeCard.classList.add("selected");

    const btnCast = document.getElementById("btnCastBallot");
    const previewChoice = document.getElementById("voterSelectedChoiceText");

    if (selectedCandidateObj) {
        if (previewChoice) previewChoice.textContent = `${selectedCandidateObj.name} (${selectedCandidateObj.party_or_slate})`;
        if (btnCast) btnCast.disabled = false;
    }
}

function openVoteConfirmModal() {
    if (!selectedCandidateObj || !currentUser.voter) {
        showToast("Please mark a candidate on the ballot paper.", "warning");
        return;
    }

    const initials = selectedCandidateObj.name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
    const avatarEl = document.getElementById("confirmCandAvatar");
    const nameEl = document.getElementById("confirmCandName");
    const partyEl = document.getElementById("confirmCandParty");
    const deptEl = document.getElementById("confirmCandDept");

    if (avatarEl) avatarEl.textContent = initials;
    if (nameEl) nameEl.textContent = selectedCandidateObj.name;
    if (partyEl) partyEl.textContent = selectedCandidateObj.party_or_slate;
    if (deptEl) deptEl.textContent = selectedCandidateObj.department;

    openModal("voteConfirmModal");
}

async function submitOfficialVote() {
    if (!selectedCandidateId || !currentUser.voter) return;
    const btn = document.getElementById("btnConfirmVoteCast");
    if (btn) {
        btn.disabled = true;
        btn.textContent = "Sealing Ballot...";
    }

    try {
        const payload = {
            voter_id: currentUser.voter.voter_id,
            election_id: currentVoterElectionId,
            candidate_id: selectedCandidateId
        };

        const res = await fetch("/api/vote", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        closeModal("voteConfirmModal");

        if (data.success) {
            showToast("Ballot recorded with SHA-256 seal!", "success");
            lastReceiptData = data;
            // Directly transition to the receipts page so the voter sees their receipt in the dedicated receipts tab
            switchVoterTab("voter-receipts");
            loadVoterReceiptsHistory();
        } else {
            showToast(data.error || "Failed to submit ballot.", "error");
            loadVoterBallot();
        }
    } catch (e) {
        showToast("Error casting vote: " + e.message, "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = "🔒 Confirm & Seal Ballot";
        }
    }
}

function populateReceiptModal(data) {
    const tokenEl = document.getElementById("rcptToken");
    const voteIdEl = document.getElementById("rcptVoteId");
    const elecEl = document.getElementById("rcptElection");
    const candEl = document.getElementById("rcptCandidate");
    const timeEl = document.getElementById("rcptTimestamp");

    if (tokenEl) tokenEl.textContent = data.receipt_token || "--";
    if (voteIdEl) voteIdEl.textContent = data.vote_id || "--";
    if (elecEl) elecEl.textContent = data.election_title || currentVoterElectionId;
    if (candEl) candEl.textContent = data.candidate_name || "Confidential Choice";
    if (timeEl) timeEl.textContent = data.timestamp || new Date().toISOString();
}

function viewVoterReceiptModal() {
    if (!lastReceiptData) return;
    populateReceiptModal(lastReceiptData);
    openModal("voteReceiptModal");
}

function copyReceiptToken() {
    const token = document.getElementById("rcptToken").textContent;
    if (token && token !== "--") {
        navigator.clipboard.writeText(token);
        showToast("Receipt token copied to clipboard!", "success");
    }
}

function printReceipt() {
    window.print();
}

// Voter Personal Receipts History
async function loadVoterReceiptsHistory() {
    const container = document.getElementById("voterReceiptsContainer");
    if (!container || !currentUser.voter) return;

    try {
        const res = await fetch(`/api/voter/my-ballots?voter_id=${encodeURIComponent(currentUser.voter.voter_id)}`);
        const data = await res.json();
        if (!data.success || !data.ballots) return;

        const votedBallots = data.ballots.filter(b => b.has_voted);
        if (votedBallots.length === 0) {
            container.innerHTML = `<div class="empty-state" style="padding: 2.5rem; text-align: center; color: var(--text-muted);">
                You have not cast any ballots yet. Go to the Polling Booth to vote in active elections!
            </div>`;
            return;
        }

        container.innerHTML = votedBallots.map(b => `
            <div class="glass-card receipt-card-item" style="padding: 1.5rem; margin-bottom: 1.25rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <span class="badge-tag badge-active">CRYPTOGRAPHICALLY SEALED</span>
                    <span style="font-family: var(--font-mono); font-size: 0.84rem; color: var(--gold); font-weight: 700;">${b.receipt_token}</span>
                </div>
                <h3 style="font-family: var(--font-heading); font-size: 1.2rem; margin-bottom: 0.35rem;">${escapeHtml(b.title)}</h3>
                <div style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.75rem;">
                    Scope: <strong>${b.election_id}</strong> (${b.category}) • Timestamp: ${b.voted_timestamp || 'SHA-256 Hashed'}
                </div>
                <button class="btn btn-secondary btn-sm" onclick="navigator.clipboard.writeText('${b.receipt_token}'); showToast('Token copied!', 'success');">
                    📋 Copy Proof Token
                </button>
            </div>
        `).join("");
    } catch (e) {
        console.error("Error loading voter receipts:", e);
    }
}

// Voter Results Tab (Enforces: Results ONLY shown if election is CLOSED by Admin)
let currentResultsElectionId = null;

async function loadVoterResults() {
    const pendingNotice = document.getElementById("voterResultsPendingNotice");
    const dataContainer = document.getElementById("voterResultsDataContainer");
    const pendingTitle = document.getElementById("voterResultsPendingTitle");
    const select = document.getElementById("voterResultsElectionSelect");
    const tbody = document.getElementById("voterResultsTableBody");

    try {
        // Fetch list of all elections if select not populated
        if (!allElectionsList || allElectionsList.length === 0) {
            const elecRes = await fetch("/api/elections?status=All");
            const elecData = await elecRes.json();
            if (elecData.success && elecData.elections) {
                allElectionsList = elecData.elections;
            }
        }

        if (select && allElectionsList && allElectionsList.length > 0) {
            if (!currentResultsElectionId) {
                currentResultsElectionId = currentVoterElectionId || allElectionsList[0].election_id;
            }
            select.innerHTML = allElectionsList.map(e => `
                <option value="${e.election_id}" ${e.election_id === currentResultsElectionId ? 'selected' : ''}>
                    ${escapeHtml(e.title)} (${e.status.toUpperCase()})
                </option>
            `).join("");
        }

        const electionId = currentResultsElectionId || "ELEC-2026-PRES";
        const res = await fetch(`/api/analytics/overview?election_id=${encodeURIComponent(electionId)}`);
        const data = await res.json();
        if (!data.success) return;

        const election = data.election || {};
        const electionStatus = (election.status || "active").toLowerCase();
        const electionTitle = election.title || electionId;

        // USER RULE: Results are ONLY shown if election is CLOSED / COMPLETED by admin!
        const isClosed = (electionStatus === "closed" || electionStatus === "completed");
        if (!isClosed) {
            if (pendingNotice) {
                pendingNotice.classList.remove("hidden");
                pendingNotice.style.display = "block";
            }
            if (pendingTitle) pendingTitle.textContent = `${electionTitle} [Status: ${electionStatus.toUpperCase()}]`;
            if (dataContainer) {
                dataContainer.classList.add("hidden");
                dataContainer.style.display = "none";
            }
            return;
        }

        // Election is closed! Show verified outcome
        if (pendingNotice) {
            pendingNotice.classList.add("hidden");
            pendingNotice.style.display = "none";
        }
        if (dataContainer) {
            dataContainer.classList.remove("hidden");
            dataContainer.style.display = "block";
        }

        const m = data.metrics || {};
        updateText("resTotalVoters", m.total_voters || 0);
        updateText("resTotalBallots", m.total_ballots || 0);
        updateText("resTurnoutRate", (m.turnout_pct || 0) + "%");

        if (m.leader) {
            updateText("resLeaderName", m.leader.name);
            updateText("resLeaderStats", `${m.leader.votes} votes (${m.leader.percentage}%)`);
        } else {
            updateText("resLeaderName", "TBD");
            updateText("resLeaderStats", "No votes recorded");
        }

        if (tbody) {
            if (!data.results || data.results.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">No votes recorded in this closed election.</td></tr>`;
                return;
            }
            tbody.innerHTML = data.results.map(r => {
                const medal = r.rank === 1 ? "🥇 " : (r.rank === 2 ? "🥈 " : (r.rank === 3 ? "🥉 " : ""));
                return `
                    <tr>
                        <td><strong>${medal}#${r.rank}</strong></td>
                        <td><strong>${escapeHtml(r.name)}</strong></td>
                        <td><span class="badge-tag">${escapeHtml(r.party_or_slate)}</span></td>
                        <td>${escapeHtml(r.department)}</td>
                        <td><strong style="color: var(--secondary-light); font-size: 1.05rem;">${r.votes}</strong></td>
                        <td><strong>${r.percentage}%</strong></td>
                    </tr>
                `;
            }).join("");
        }
    } catch (e) {
        console.error("Error loading voter results:", e);
    }
}

function onVoterResultsElectionChange() {
    const select = document.getElementById("voterResultsElectionSelect");
    if (!select) return;
    currentResultsElectionId = select.value;
    loadVoterResults();
}

// =============================================================================
// ADMIN PORTAL: VOTER APPROVAL QUEUE & MANAGEMENT
// =============================================================================
function switchAdminTab(tabKey) {
    // Hide all admin panes
    document.querySelectorAll(".admin-tab-pane").forEach(p => {
        p.classList.remove("active");
        p.classList.add("hidden");
    });
    document.querySelectorAll("#adminNavGroup .nav-tab").forEach(t => t.classList.remove("active"));

    const targetPane = document.getElementById(`admin-tab-${tabKey}`);
    if (targetPane) {
        targetPane.classList.remove("hidden");
        targetPane.classList.add("active");
    }

    const activeNav = document.querySelector(`#adminNavGroup .nav-tab[data-tab="admin-${tabKey}"]`);
    if (activeNav) activeNav.classList.add("active");

    if (tabKey === "queue") {
        loadPendingVotersQueue();
    } else if (tabKey === "elections") {
        loadAdminElectionsTable();
    } else if (tabKey === "candidates") {
        loadAdminCandidatesTable();
    } else if (tabKey === "results") {
        loadAdminAnalytics();
    } else if (tabKey === "audit") {
        loadAdminAuditLogs();
    }
}

// Inline Create Election Form handlers
function toggleInlineCreateElection() {
    const card = document.getElementById("adminInlineElectionCard");
    if (!card) return;
    card.classList.toggle("hidden");
    if (!card.classList.contains("hidden")) {
        const idInput = document.getElementById("inlineElecId");
        if (idInput) {
            idInput.value = "ELEC-2026-" + Math.floor(1000 + Math.random() * 9000);
            idInput.focus();
        }
    }
}

async function handleInlineCreateElection(e) {
    e.preventDefault();
    const btn = document.getElementById("btnSubmitInlineElec");
    if (btn) btn.disabled = true;

    const payload = {
        election_id: document.getElementById("inlineElecId").value.trim().toUpperCase(),
        title: document.getElementById("inlineElecTitle").value.trim(),
        category: document.getElementById("inlineElecCat").value,
        status: document.getElementById("inlineElecStatus").value,
        description: document.getElementById("inlineElecDesc").value.trim()
    };

    try {
        const res = await fetch("/api/elections", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Election '${payload.election_id}' registered successfully!`, "success");
            toggleInlineCreateElection();
            loadAdminElectionsTable();
        } else {
            showToast(data.error || "Failed to create election.", "error");
        }
    } catch (err) {
        showToast("Error: " + err.message, "error");
    } finally {
        if (btn) btn.disabled = false;
    }
}

// Inline Add Candidate / Contestant Form handlers
function toggleInlineAddCandidate() {
    const card = document.getElementById("adminInlineCandidateCard");
    if (!card) return;
    card.classList.toggle("hidden");

    if (!card.classList.contains("hidden")) {
        // Populate election select options
        const select = document.getElementById("inlineCandElectionId");
        if (select && allElectionsList && allElectionsList.length > 0) {
            select.innerHTML = allElectionsList.map(e => `
                <option value="${e.election_id}">${escapeHtml(e.title)}</option>
            `).join("");
        }
        const nameInput = document.getElementById("inlineCandName");
        if (nameInput) nameInput.focus();
    }
}

async function handleInlineAddCandidate(e) {
    e.preventDefault();
    const btn = document.getElementById("btnSubmitInlineCand");
    if (btn) btn.disabled = true;

    const eleId = document.getElementById("inlineCandElectionId").value;
    const name = document.getElementById("inlineCandName").value.trim();
    const party = document.getElementById("inlineCandParty").value.trim();
    const dept = document.getElementById("inlineCandDept").value;
    const manifesto = document.getElementById("inlineCandManifesto").value.trim();
    const candId = "CAND-" + Math.floor(10 + Math.random() * 90);

    try {
        const res = await fetch("/api/candidates", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                election_id: eleId,
                candidate_id: candId,
                name: name,
                party_or_slate: party,
                department: dept,
                manifesto: manifesto
            })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Contestant '${name}' successfully registered into election!`, "success");
            toggleInlineAddCandidate();
            // Switch filter to this election and refresh table
            const filterSelect = document.getElementById("adminCandidateElectionFilter");
            if (filterSelect) filterSelect.value = eleId;
            currentAdminElectionId = eleId;
            loadAdminCandidatesTable();
        } else {
            showToast(data.error || "Failed to add candidate.", "error");
        }
    } catch (err) {
        showToast("Error: " + err.message, "error");
    } finally {
        if (btn) btn.disabled = false;
    }
}

async function loadPendingVotersQueue() {
    const pendingTbody = document.getElementById("pendingVotersTableBody");
    const activeTbody = document.getElementById("activeVotersTableBody");
    const countBadge = document.getElementById("pendingVotersCountBadge");

    try {
        // 1. Fetch pending voters
        const pendingRes = await fetch("/api/admin/pending-voters");
        const pendingData = await pendingRes.json();
        const pendingList = pendingData.pending_voters || [];

        if (countBadge) {
            countBadge.textContent = pendingList.length;
            if (pendingList.length > 0) {
                countBadge.classList.remove("hidden");
            } else {
                countBadge.classList.add("hidden");
            }
        }

        if (pendingTbody) {
            if (pendingList.length === 0) {
                pendingTbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                    No pending voter applications. New voter registrations will appear here for verification!
                </td></tr>`;
            } else {
                pendingTbody.innerHTML = pendingList.map(v => `
                    <tr>
                        <td><strong>${escapeHtml(v.voter_id)}</strong></td>
                        <td>${escapeHtml(v.name)}</td>
                        <td>${escapeHtml(v.email)}</td>
                        <td><span class="badge-tag">${escapeHtml(v.department)}</span></td>
                        <td>Year ${v.year_of_study}</td>
                        <td>${v.age}</td>
                        <td><span class="badge-tag badge-draft">PENDING APPROVAL</span></td>
                        <td>
                            <div style="display: flex; gap: 0.4rem;">
                                <button class="btn btn-primary btn-sm" onclick="handleApproveVoter('${v.voter_id}')">
                                    ✅ Approve &amp; Verify
                                </button>
                                <button class="btn btn-danger btn-sm" onclick="handleRejectVoter('${v.voter_id}')">
                                    ❌ Reject
                                </button>
                            </div>
                        </td>
                    </tr>
                `).join("");
            }
        }

        // 2. Fetch approved active voters
        const activeRes = await fetch("/api/voters?status=active");
        const activeData = await activeRes.json();
        const activeList = activeData.voters || [];

        if (activeTbody) {
            if (activeList.length === 0) {
                activeTbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">
                    No approved voters yet. Review and approve pending signups above to grant voting eligibility.
                </td></tr>`;
            } else {
                activeTbody.innerHTML = activeList.map(v => `
                    <tr>
                        <td><strong>${escapeHtml(v.voter_id)}</strong></td>
                        <td>${escapeHtml(v.name)}</td>
                        <td>${escapeHtml(v.email)}</td>
                        <td><span class="badge-tag">${escapeHtml(v.department)}</span></td>
                        <td>Year ${v.year_of_study}</td>
                        <td>${v.age}</td>
                        <td><span class="badge-tag badge-active">ELIGIBLE / ACTIVE</span></td>
                        <td>
                            <button class="btn btn-danger btn-sm" onclick="handleRejectVoter('${v.voter_id}')">
                                Remove
                            </button>
                        </td>
                    </tr>
                `).join("");
            }
        }
    } catch (e) {
        console.error("Error loading pending queue:", e);
    }
}

async function handleApproveVoter(voterId) {
    try {
        const res = await fetch("/api/admin/approve-voter", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ voter_id: voterId })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Voter '${voterId}' approved by Administrator! They may now log in and vote.`, "success");
            loadPendingVotersQueue();
        } else {
            showToast(data.error || "Approval failed.", "error");
        }
    } catch (e) {
        showToast("Error: " + e.message, "error");
    }
}

async function handleRejectVoter(voterId) {
    if (!confirm(`Are you sure you want to reject and remove registration '${voterId}'?`)) return;

    try {
        const res = await fetch("/api/admin/reject-voter", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ voter_id: voterId })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Voter application '${voterId}' removed.`, "info");
            loadPendingVotersQueue();
        } else {
            showToast(data.error || "Action failed.", "error");
        }
    } catch (e) {
        showToast("Error: " + e.message, "error");
    }
}

async function purgeAllVotersAndVotes() {
    if (!confirm("Are you sure you want to purge all existing voters and votes? This clears the database for a clean start where voters register their own accounts.")) return;

    try {
        const res = await fetch("/api/admin/purge-voters", { method: "POST" });
        const data = await res.json();
        if (data.success) {
            showToast("All legacy voters and ballots cleared. System ready for live sign-ups!", "success");
            loadPendingVotersQueue();
        }
    } catch (e) {
        showToast("Error: " + e.message, "error");
    }
}

// =============================================================================
// ADMIN PORTAL: ELECTIONS MANAGEMENT & LIFECYCLE
// =============================================================================
async function loadAdminElectionsTable() {
    const tbody = document.getElementById("adminElectionsTableBody");
    const candSelect = document.getElementById("adminCandidateElectionFilter");
    const modalSelect = document.getElementById("newCandElectionId");
    if (!tbody) return;

    try {
        const res = await fetch("/api/elections?status=All");
        const data = await res.json();
        if (!data.success || !data.elections) return;
        allElectionsList = data.elections;

        // Populate dropdowns
        if (candSelect) {
            candSelect.innerHTML = allElectionsList.map(e => `
                <option value="${e.election_id}" ${e.election_id === currentAdminElectionId ? 'selected' : ''}>
                    ${escapeHtml(e.title)} (${e.status.toUpperCase()})
                </option>
            `).join("");
            if (!currentAdminElectionId && allElectionsList.length > 0) {
                currentAdminElectionId = allElectionsList[0].election_id;
            }
        }

        if (modalSelect) {
            modalSelect.innerHTML = allElectionsList.map(e => `
                <option value="${e.election_id}">${escapeHtml(e.title)}</option>
            `).join("");
        }

        tbody.innerHTML = allElectionsList.map(ele => {
            const statusClass = ele.status === "active" ? "badge-active" : (ele.status === "completed" ? "badge-completed" : "badge-draft");
            const visibilityText = ele.status === "active" ? "✅ Visible & Open to Voters" : (ele.status === "completed" ? "🔒 Closed (Results Certified)" : "❌ Draft (Hidden from Voters)");

            return `
                <tr>
                    <td><strong>${escapeHtml(ele.election_id)}</strong></td>
                    <td>${escapeHtml(ele.title)}</td>
                    <td><span class="badge-tag">${escapeHtml(ele.category)}</span></td>
                    <td><span class="badge-tag ${statusClass}">${(ele.status).toUpperCase()}</span></td>
                    <td style="font-size: 0.82rem; font-weight: 600;">${visibilityText}</td>
                    <td>
                        <div style="display: flex; gap: 0.4rem; flex-wrap: wrap;">
                            ${ele.status !== 'active' 
                                ? `<button class="btn btn-primary btn-sm" onclick="handleAcceptElection('${ele.election_id}')">
                                    ✅ Accept &amp; Open to Voters
                                   </button>` 
                                : `<button class="btn btn-gold btn-sm" onclick="handleCloseElection('${ele.election_id}')">
                                    🔒 Close Election
                                   </button>`
                            }
                            <button class="btn btn-danger btn-sm" onclick="handleDeleteElectionAdmin('${ele.election_id}')">
                                Delete
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        console.error("Error loading admin elections:", e);
    }
}

async function handleAcceptElection(electionId) {
    try {
        const res = await fetch("/api/admin/accept-election", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ election_id: electionId })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Election '${electionId}' accepted by Administrator! It is now live for voters.`, "success");
            loadAdminElectionsTable();
        } else {
            showToast(data.error || "Action failed.", "error");
        }
    } catch (e) {
        showToast("Error: " + e.message, "error");
    }
}

async function handleCloseElection(electionId) {
    if (!confirm(`Close voting for election '${electionId}'? This will terminate live balloting and certify final results.`)) return;

    try {
        const res = await fetch("/api/admin/close-election", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ election_id: electionId })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Election '${electionId}' closed by Administrator. Final results certified!`, "info");
            loadAdminElectionsTable();
        } else {
            showToast(data.error || "Action failed.", "error");
        }
    } catch (e) {
        showToast("Error: " + e.message, "error");
    }
}

function openCreateElectionModal() {
    openModal("createElectionModal");
}

async function handleCreateElectionSubmit(e) {
    e.preventDefault();
    const id = document.getElementById("newElecId").value.trim().toUpperCase();
    const title = document.getElementById("newElecTitle").value.trim();
    const category = document.getElementById("newElecCat").value;
    const desc = document.getElementById("newElecDesc").value.trim();

    try {
        const res = await fetch("/api/elections", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                election_id: id,
                title: title,
                category: category,
                description: desc
            })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Election '${id}' created in draft! Click 'Accept & Open' when ready.`, "success");
            closeModal("createElectionModal");
            document.getElementById("createElectionForm").reset();
            loadAdminElectionsTable();
        } else {
            showToast(data.error || "Creation failed.", "error");
        }
    } catch (err) {
        showToast("Error: " + err.message, "error");
    }
}

async function handleDeleteElectionAdmin(electionId) {
    if (!confirm(`Delete election '${electionId}'?`)) return;

    try {
        const res = await fetch(`/api/elections/${encodeURIComponent(electionId)}`, {
            method: "DELETE"
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Election '${electionId}' deleted.`, "success");
            loadAdminElectionsTable();
        } else {
            showToast(data.error || "Could not delete election.", "error");
        }
    } catch (e) {
        showToast("Error: " + e.message, "error");
    }
}

// =============================================================================
// ADMIN PORTAL: CANDIDATES MANAGEMENT
// =============================================================================
async function loadAdminCandidatesTable() {
    const tbody = document.getElementById("adminCandidatesTableBody");
    const select = document.getElementById("adminCandidateElectionFilter");
    if (!tbody) return;

    const electionId = select && select.value ? select.value : (currentAdminElectionId || "ELEC-2026-PRES");

    try {
        const res = await fetch(`/api/candidates?election_id=${encodeURIComponent(electionId)}`);
        const data = await res.json();
        if (!data.success || !data.candidates) return;

        if (data.candidates.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                No candidates registered for this election. Click '+ Add Candidate' to create one!
            </td></tr>`;
            return;
        }

        tbody.innerHTML = data.candidates.map(cand => `
            <tr>
                <td><strong>${escapeHtml(cand.candidate_id)}</strong></td>
                <td>${escapeHtml(cand.name)}</td>
                <td><span class="badge-tag">${escapeHtml(cand.party_or_slate)}</span></td>
                <td>${escapeHtml(cand.department)}</td>
                <td style="max-width: 320px; font-size: 0.82rem; color: var(--text-secondary);">${escapeHtml(cand.manifesto)}</td>
                <td><strong style="color: var(--gold); font-size: 1.1rem;">${cand.vote_count !== undefined ? cand.vote_count : 0}</strong></td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="handleDeleteCandidateAdmin('${cand.candidate_id}')">
                        Delete
                    </button>
                </td>
            </tr>
        `).join("");
    } catch (e) {
        console.error("Error loading admin candidates:", e);
    }
}

function openAddCandidateModal() {
    openModal("addCandidateModal");
}

async function handleAddCandidateSubmit(e) {
    e.preventDefault();
    const eleId = document.getElementById("newCandElectionId").value;
    const candId = document.getElementById("newCandId").value.trim().toUpperCase();
    const name = document.getElementById("newCandName").value.trim();
    const party = document.getElementById("newCandParty").value.trim();
    const dept = document.getElementById("newCandDept").value;
    const manifesto = document.getElementById("newCandManifesto").value.trim();

    try {
        const res = await fetch("/api/candidates", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                election_id: eleId,
                candidate_id: candId,
                name: name,
                party_or_slate: party,
                department: dept,
                manifesto: manifesto
            })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Candidate '${name}' added to election '${eleId}'!`, "success");
            closeModal("addCandidateModal");
            document.getElementById("addCandidateForm").reset();
            loadAdminCandidatesTable();
        } else {
            showToast(data.error || "Failed to add candidate.", "error");
        }
    } catch (err) {
        showToast("Error: " + err.message, "error");
    }
}

async function handleDeleteCandidateAdmin(candidateId) {
    if (!confirm(`Delete candidate '${candidateId}'?`)) return;

    try {
        const res = await fetch(`/api/candidates/${encodeURIComponent(candidateId)}`, {
            method: "DELETE"
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Candidate '${candidateId}' deleted.`, "success");
            loadAdminCandidatesTable();
        } else {
            showToast(data.error || "Could not delete candidate.", "error");
        }
    } catch (e) {
        showToast("Error: " + e.message, "error");
    }
}

// =============================================================================
// ADMIN PORTAL: ANALYTICS & AUDIT LOGS
// =============================================================================
async function loadAdminAnalytics() {
    const electionId = currentAdminElectionId || "ELEC-2026-PRES";
    const tbody = document.getElementById("adminResultsTableBody");

    try {
        const res = await fetch(`/api/analytics/overview?election_id=${encodeURIComponent(electionId)}`);
        const data = await res.json();
        if (!data.success) return;

        if (tbody) {
            if (!data.results || data.results.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">No ballots recorded yet.</td></tr>`;
            } else {
                tbody.innerHTML = data.results.map(r => `
                    <tr>
                        <td><strong>#${r.rank}</strong></td>
                        <td><code>${r.candidate_id}</code></td>
                        <td><strong>${escapeHtml(r.name)}</strong></td>
                        <td><span class="badge-tag">${escapeHtml(r.party_or_slate)}</span></td>
                        <td>${escapeHtml(r.department)}</td>
                        <td><strong style="color: var(--secondary-light); font-size: 1.05rem;">${r.votes}</strong></td>
                        <td><strong>${r.percentage}%</strong></td>
                    </tr>
                `).join("");
            }
        }

        renderAdminCandidateVotesChart(data.results);
        renderAdminDepartmentTurnoutChart(data.department_turnout);

    } catch (e) {
        console.error("Error loading admin analytics:", e);
    }
}

function renderAdminCandidateVotesChart(results) {
    const canvas = document.getElementById("adminCandidateVotesChart");
    if (!canvas) return;

    const labels = (results || []).map(r => r.name);
    const votes = (results || []).map(r => r.votes);

    if (adminCandidateVotesChart) adminCandidateVotesChart.destroy();

    adminCandidateVotesChart = new Chart(canvas, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Verified Ballots Cast",
                data: votes,
                backgroundColor: "rgba(99, 102, 241, 0.75)",
                borderColor: "#6366f1",
                borderWidth: 1.5,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0, color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
                x: { ticks: { color: "#cbd5e1" }, grid: { display: false } }
            }
        }
    });
}

function renderAdminDepartmentTurnoutChart(turnoutData) {
    const canvas = document.getElementById("adminDepartmentTurnoutChart");
    if (!canvas) return;

    const labels = (turnoutData || []).map(t => t.department);
    const counts = (turnoutData || []).map(t => t.ballots_cast);

    if (adminDepartmentTurnoutChart) adminDepartmentTurnoutChart.destroy();

    adminDepartmentTurnoutChart = new Chart(canvas, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: ["#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6"],
                borderColor: "#0c1222",
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: "right", labels: { color: "#cbd5e1", font: { size: 11 } } } }
        }
    });
}

async function loadAdminAuditLogs() {
    const tbody = document.getElementById("adminAuditTableBody");
    if (!tbody) return;

    try {
        const res = await fetch("/api/audit-logs");
        const data = await res.json();
        if (!data.success || !data.logs) return;

        tbody.innerHTML = data.logs.map(log => `
            <tr>
                <td style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--secondary-light);">${log.timestamp}</td>
                <td><span class="badge-tag" style="border-color: rgba(99, 102, 241, 0.4);">${log.action}</span></td>
                <td><code style="font-size: 0.78rem; color: var(--text-muted);">${JSON.stringify(log.details)}</code></td>
            </tr>
        `).join("");
    } catch (e) {
        console.error("Error loading audit logs:", e);
    }
}

// =============================================================================
// UTILITIES
// =============================================================================
function openModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove("hidden");
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add("hidden");
}

function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    const icon = type === "success" ? "✓" : (type === "error" ? "✕" : (type === "warning" ? "⚠️" : "ℹ️"));
    toast.innerHTML = `<span style="font-weight: 800;">${icon}</span><span>${escapeHtml(message)}</span>`;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

function updateText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
