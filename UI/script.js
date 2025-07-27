// Global state management for user data flow
const UserDataFlow = {
    userData: {
        account: {
            name: '',
            email: '',
            password: '',
            confirmPassword: ''
        },
        profile: {
            name: '',
            photo: null,
            phoneNumber: '',
            role: '',
            department: ''
        },
        members: [],
        documents: [],
        isComplete: false
    },
    
    currentStep: 1,
    totalSteps: 5,
    
    // Save data for current step
    saveStepData(step, data) {
        switch(step) {
            case 1:
                this.userData.account = {...this.userData.account, ...data};
                break;
            case 2:
                this.userData.profile = {...this.userData.profile, ...data};
                break;
            case 3:
                this.userData.members = data;
                break;
            case 4:
                this.userData.documents = data;
                break;
            case 5:
                this.userData.isComplete = true;
                break;
        }
        
        // Save to localStorage for persistence
        localStorage.setItem('redAerialUserData', JSON.stringify(this.userData));
        this.updateProgress();
    },
    
    // Load data from localStorage
    loadUserData() {
        const saved = localStorage.getItem('redAerialUserData');
        if (saved) {
            this.userData = {...this.userData, ...JSON.parse(saved)};
        }
    },
    
    // Update progress indicator
    updateProgress() {
        const progressPercentage = (this.currentStep / this.totalSteps) * 100;
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = progressPercentage + '%';
        }
        
        // Update step indicators
        const steps = document.querySelectorAll('.step');
        steps.forEach((step, index) => {
            step.classList.remove('completed', 'active');
            if (index < this.currentStep - 1) {
                step.classList.add('completed');
            } else if (index === this.currentStep - 1) {
                step.classList.add('active');
            }
        });
    },
    
    // Validate current step data
    validateCurrentStep() {
        switch(this.currentStep) {
            case 1:
                return this.validateAccountData();
            case 2:
                return this.validateProfileData();
            case 3:
                return this.validateMembersData();
            case 4:
                return this.validateDocumentsData();
            case 5:
                return true; // Review step, no validation needed
            default:
                return false;
        }
    },
    
    validateAccountData() {
        const form = document.getElementById('signupForm');
        const name = form.querySelector('#name')?.value?.trim() || '';
        const email = form.querySelector('#email')?.value?.trim() || '';
        const password = form.querySelector('#password')?.value || '';
        const confirmPassword = form.querySelector('#confirmPassword')?.value || '';
        
        const errors = [];
        
        if (name.length < 2) errors.push('Name must be at least 2 characters long');
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.push('Please enter a valid email address');
        if (password.length < 8) errors.push('Password must be at least 8 characters long');
        if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password)) errors.push('Password must contain uppercase, lowercase, and number');
        if (password !== confirmPassword) errors.push('Passwords do not match');
        
        if (errors.length === 0) {
            this.saveStepData(1, { name, email, password, confirmPassword });
            return true;
        } else {
            this.showValidationErrors(errors);
            return false;
        }
    },
    
    validateProfileData() {
        const name = document.getElementById('profileName')?.value?.trim() || '';
        const phoneNumber = document.getElementById('phoneNumber')?.value?.trim() || '';
        const role = document.getElementById('role')?.value?.trim() || '';
        const department = document.getElementById('department')?.value || '';
        
        const errors = [];
        
        if (name.length < 2) errors.push('Profile name must be at least 2 characters long');
        if (!/^\+?[\d\s\-\(\)]+$/.test(phoneNumber)) errors.push('Please enter a valid phone number');
        if (role.length < 2) errors.push('Role must be specified');
        if (!department) errors.push('Please select a department');
        
        if (errors.length === 0) {
            this.saveStepData(2, { name, phoneNumber, role, department });
            return true;
        } else {
            this.showValidationErrors(errors);
            return false;
        }
    },
    
    validateMembersData() {
        const memberInputs = document.querySelectorAll('.member-item input[readonly]');
        const members = Array.from(memberInputs).map(input => input.value.trim()).filter(value => value);
        
        this.saveStepData(3, members);
        return true; // Members are optional
    },
    
    validateDocumentsData() {
        const uploadedDocs = document.querySelectorAll('.upload-area.uploaded');
        const documents = Array.from(uploadedDocs).map(area => area.dataset.fileName);
        
        this.saveStepData(4, documents);
        return true; // Documents are optional
    },
    
    showValidationErrors(errors) {
        // Clear previous errors
        document.querySelectorAll('.validation-error').forEach(error => error.remove());
        
        // Create error container
        const errorContainer = document.createElement('div');
        errorContainer.className = 'validation-error';
        errorContainer.innerHTML = `
            <div class="error-content">
                <i class="fas fa-exclamation-triangle"></i>
                <div class="error-messages">
                    ${errors.map(error => `<p>${error}</p>`).join('')}
                </div>
            </div>
        `;
        
        const formContainer = document.querySelector('.form-container');
        formContainer.insertBefore(errorContainer, formContainer.firstChild);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            errorContainer.remove();
        }, 5000);
    }
};

// Initialize data flow on page load
document.addEventListener('DOMContentLoaded', function() {
    UserDataFlow.loadUserData();
    UserDataFlow.updateProgress();
    
    // Add progress bar to sidebar
    const sidebar = document.querySelector('.sidebar');
    const progressHTML = `
        <div class="progress-section">
            <div class="progress-label">Setup Progress</div>
            <div class="progress-container">
                <div class="progress-bar"></div>
            </div>
            <div class="progress-text">${UserDataFlow.currentStep}/${UserDataFlow.totalSteps} Complete</div>
        </div>
    `;
    
    const stepsContainer = document.querySelector('.steps-container');
    stepsContainer.insertAdjacentHTML('beforebegin', progressHTML);
    UserDataFlow.updateProgress();
});

// Password toggle functionality
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const toggleIcon = document.getElementById(inputId + 'Toggle');
    
    if (input.type === 'password') {
        input.type = 'text';
        toggleIcon.className = 'fas fa-eye-slash';
    } else {
        input.type = 'password';
        toggleIcon.className = 'fas fa-eye';
    }
}

// Form validation
function validateForm() {
    return UserDataFlow.validateCurrentStep();
}

// Show error message
function showError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    errorDiv.style.color = '#ff4444';
    errorDiv.style.fontSize = '12px';
    errorDiv.style.marginTop = '4px';
    
    field.parentNode.appendChild(errorDiv);
    field.style.borderColor = '#ff4444';
}

// Clear error messages
function clearErrors() {
    const errorMessages = document.querySelectorAll('.error-message');
    errorMessages.forEach(error => error.remove());
    
    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => {
        input.style.borderColor = 'rgba(255, 255, 255, 0.2)';
    });
}

// Form submission
document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('submit', function(e) {
        if (e.target.id === 'signupForm') {
            e.preventDefault();
            
            if (UserDataFlow.validateCurrentStep()) {
                // Show loading state
                const submitBtn = document.querySelector('.signup-btn');
                const originalText = submitBtn.textContent;
                submitBtn.textContent = 'Processing...';
                submitBtn.disabled = true;
                
                // Simulate API call with user data
                setTimeout(() => {
                    console.log('User data being sent:', UserDataFlow.userData);
                    showSuccessMessage('Account created successfully! Moving to next step...');
                    
                    // Reset button
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                    
                    // Move to next step
                    nextStep();
                }, 1500);
            }
        }
    });
});

// Step navigation
function nextStep() {
    if (!UserDataFlow.validateCurrentStep()) {
        return false;
    }
    
    const currentStep = document.querySelector('.step.active');
    const nextStep = currentStep.nextElementSibling;
    
    if (nextStep && nextStep.classList.contains('step')) {
        UserDataFlow.currentStep++;
        currentStep.classList.remove('active');
        currentStep.classList.add('completed');
        nextStep.classList.add('active');
        
        // Update form content based on step
        updateFormContent(nextStep);
        UserDataFlow.updateProgress();
        updateProgressText();
    }
}

function previousStep() {
    if (UserDataFlow.currentStep > 1) {
        const currentStep = document.querySelector('.step.active');
        const prevStep = currentStep.previousElementSibling;
        
        if (prevStep && prevStep.classList.contains('step')) {
            UserDataFlow.currentStep--;
            currentStep.classList.remove('active');
            prevStep.classList.remove('completed');
            prevStep.classList.add('active');
            
            updateFormContent(prevStep);
            UserDataFlow.updateProgress();
            updateProgressText();
        }
    }
}

function updateProgressText() {
    const progressText = document.querySelector('.progress-text');
    if (progressText) {
        progressText.textContent = `${UserDataFlow.currentStep}/${UserDataFlow.totalSteps} Complete`;
    }
}

function updateFormContent(step) {
    const stepText = step.querySelector('span').textContent;
    const formHeader = document.querySelector('.form-header h1');
    const formDescription = document.querySelector('.form-header p');
    const formContainer = document.querySelector('.signup-form');
    
    switch(stepText) {
        case 'Create Your Account':
            formHeader.textContent = 'Create Your Account';
            formDescription.textContent = 'Use your work email for secure access.';
            formContainer.innerHTML = `
                <button type="button" class="google-btn">
                    <img src="https://developers.google.com/identity/images/g-logo.png" alt="Google" class="google-icon">
                    Sign Up with Google
                </button>

                <div class="divider">
                    <span>or</span>
                </div>

                <div class="form-group">
                    <label for="name">Name</label>
                    <input type="text" id="name" name="name" value="${UserDataFlow.userData.account.name || 'Sam Andreas'}" required>
                </div>

                <div class="form-group">
                    <label for="email">Email ID</label>
                    <div class="input-wrapper">
                        <input type="email" id="email" name="email" value="${UserDataFlow.userData.account.email || 'samandreas23@gmail.com'}" required>
                        <span class="input-status valid">
                            <i class="fas fa-check"></i>
                        </span>
                    </div>
                </div>

                <div class="form-group">
                    <label for="password">Password</label>
                    <div class="input-wrapper">
                        <input type="password" id="password" name="password" placeholder="Enter a secure password" required>
                        <span class="toggle-password" onclick="togglePassword('password')">
                            <i class="fas fa-eye" id="passwordToggle"></i>
                        </span>
                    </div>
                </div>

                <div class="form-group">
                    <label for="confirmPassword">Re-Enter Password</label>
                    <div class="input-wrapper">
                        <input type="password" id="confirmPassword" name="confirmPassword" placeholder="Confirm your password" required>
                        <span class="toggle-password" onclick="togglePassword('confirmPassword')">
                            <i class="fas fa-eye" id="confirmPasswordToggle"></i>
                        </span>
                    </div>
                </div>

                <div class="form-navigation">
                    <button type="submit" class="signup-btn">Create Account & Continue</button>
                </div>

                <div class="signin-link">
                    <span>Already have an account? <a href="#" onclick="showSignIn()">Sign In</a></span>
                </div>
            `;
            break;
            
        case 'Set up your profile':
            formHeader.textContent = 'Set up your profile';
            formDescription.textContent = 'This info will be visible for contact.';
            formContainer.innerHTML = `
                <div class="form-group">
                    <label for="profileName">Name</label>
                    <input type="text" id="profileName" name="profileName" value="${UserDataFlow.userData.profile.name || UserDataFlow.userData.account.name || 'Sam Andreas'}" required>
                </div>

                <div class="form-group">
                    <label for="profilePhoto">Upload profile photo</label>
                    <div class="upload-area" onclick="triggerFileUpload('profilePhoto')">
                        <div class="upload-content">
                            <i class="fas fa-camera" style="font-size: 24px; color: #00d4aa; margin-bottom: 10px;"></i>
                            <p style="color: #888; font-size: 14px;">Click to upload photo</p>
                        </div>
                        <input type="file" id="profilePhoto" accept="image/*" style="display: none;" onchange="handleFileUpload(this, 'profilePhoto')">
                    </div>
                </div>

                <div class="form-group">
                    <label for="phoneNumber">Phone Number</label>
                    <input type="tel" id="phoneNumber" name="phoneNumber" value="${UserDataFlow.userData.profile.phoneNumber || '91+ 123456789'}" required>
                </div>

                <div class="form-group">
                    <label for="role">Role</label>
                    <input type="text" id="role" name="role" value="${UserDataFlow.userData.profile.role || 'Drone Operator'}" required>
                </div>

                <div class="form-group">
                    <label for="department">Department</label>
                    <div class="select-wrapper">
                        <select id="department" name="department" required>
                            <option value="Operations" ${UserDataFlow.userData.profile.department === 'Operations' ? 'selected' : ''}>Operations</option>
                            <option value="Engineering" ${UserDataFlow.userData.profile.department === 'Engineering' ? 'selected' : ''}>Engineering</option>
                            <option value="Sales" ${UserDataFlow.userData.profile.department === 'Sales' ? 'selected' : ''}>Sales</option>
                            <option value="Support" ${UserDataFlow.userData.profile.department === 'Support' ? 'selected' : ''}>Support</option>
                            <option value="Management" ${UserDataFlow.userData.profile.department === 'Management' ? 'selected' : ''}>Management</option>
                        </select>
                        <i class="fas fa-chevron-down select-arrow"></i>
                    </div>
                </div>

                <div class="form-navigation">
                    <button type="button" class="btn-secondary" onclick="previousStep()">
                        <i class="fas fa-arrow-left"></i> Previous
                    </button>
                    <button type="button" class="signup-btn" onclick="nextStep()">
                        Continue <i class="fas fa-arrow-right"></i>
                    </button>
                </div>
            `;
            break;
            
        case 'Invite Members':
            formHeader.textContent = 'Invite members';
            formDescription.textContent = 'You can invite up to 5 members to your team.';
            
            let membersHTML = '';
            for (let i = 0; i < 5; i++) {
                const memberValue = UserDataFlow.userData.members[i] || '';
                const isReadonly = memberValue ? 'readonly' : '';
                const buttonIcon = memberValue ? 'fa-minus' : 'fa-plus';
                const buttonClass = memberValue ? 'remove-member' : 'add-member-btn';
                const buttonAction = memberValue ? 'removeMember(this)' : 'addMember(this)';
                
                membersHTML += `
                    <div class="member-item">
                        <label>Member ${String(i + 1).padStart(2, '0')}</label>
                        <div class="member-input-wrapper">
                            <input type="email" value="${memberValue}" placeholder="Invite member ${i + 1}" ${isReadonly}>
                            <button type="button" class="${buttonClass}" onclick="${buttonAction}">
                                <i class="fas ${buttonIcon}"></i>
                            </button>
                        </div>
                    </div>
                `;
            }
            
            formContainer.innerHTML = `
                <div class="members-list">
                    ${membersHTML}
                </div>

                <div class="form-navigation">
                    <button type="button" class="btn-secondary" onclick="previousStep()">
                        <i class="fas fa-arrow-left"></i> Previous
                    </button>
                    <button type="button" class="signup-btn" onclick="nextStep()">
                        Continue <i class="fas fa-arrow-right"></i>
                    </button>
                </div>
            `;
            break;
            
        case 'Upload Documents':
            formHeader.textContent = 'Upload Documents';
            formDescription.textContent = 'Upload important documents for verification.';
            formContainer.innerHTML = `
                <div class="document-upload-section">
                    <div class="form-group">
                        <label>ID Proof (Optional)</label>
                        <div class="upload-area" onclick="triggerFileUpload('idProof')">
                            <div class="upload-content">
                                <i class="fas fa-file-upload" style="font-size: 24px; color: #00d4aa; margin-bottom: 10px;"></i>
                                <p style="color: #888; font-size: 14px;">Click to upload ID proof</p>
                            </div>
                            <input type="file" id="idProof" accept=".pdf,.jpg,.jpeg,.png" style="display: none;" onchange="handleFileUpload(this, 'idProof')">
                        </div>
                    </div>

                    <div class="form-group">
                        <label>License/Certificate (Optional)</label>
                        <div class="upload-area" onclick="triggerFileUpload('license')">
                            <div class="upload-content">
                                <i class="fas fa-certificate" style="font-size: 24px; color: #00d4aa; margin-bottom: 10px;"></i>
                                <p style="color: #888; font-size: 14px;">Click to upload license</p>
                            </div>
                            <input type="file" id="license" accept=".pdf,.jpg,.jpeg,.png" style="display: none;" onchange="handleFileUpload(this, 'license')">
                        </div>
                    </div>
                </div>

                <div class="form-navigation">
                    <button type="button" class="btn-secondary" onclick="previousStep()">
                        <i class="fas fa-arrow-left"></i> Previous
                    </button>
                    <button type="button" class="signup-btn" onclick="nextStep()">
                        Continue <i class="fas fa-arrow-right"></i>
                    </button>
                </div>
            `;
            break;
            
        case 'Complete Sign In':
            formHeader.textContent = 'Review & Complete';
            formDescription.textContent = 'Review your information and complete the setup.';
            formContainer.innerHTML = `
                <div class="review-form">
                    <div class="review-section">
                        <h3><i class="fas fa-user"></i> Account Information</h3>
                        <div class="review-item">
                            <span class="label">Name:</span>
                            <span class="value">${UserDataFlow.userData.account.name}</span>
                        </div>
                        <div class="review-item">
                            <span class="label">Email:</span>
                            <span class="value">${UserDataFlow.userData.account.email}</span>
                        </div>
                    </div>

                    <div class="review-section">
                        <h3><i class="fas fa-id-card"></i> Profile Information</h3>
                        <div class="review-item">
                            <span class="label">Role:</span>
                            <span class="value">${UserDataFlow.userData.profile.role}</span>
                        </div>
                        <div class="review-item">
                            <span class="label">Department:</span>
                            <span class="value">${UserDataFlow.userData.profile.department}</span>
                        </div>
                        <div class="review-item">
                            <span class="label">Phone:</span>
                            <span class="value">${UserDataFlow.userData.profile.phoneNumber}</span>
                        </div>
                    </div>

                    <div class="review-section">
                        <h3><i class="fas fa-users"></i> Team Members</h3>
                        <div class="review-item">
                            <span class="label">Invited:</span>
                            <span class="value">${UserDataFlow.userData.members.length} member(s)</span>
                        </div>
                    </div>
                </div>

                <div class="form-navigation">
                    <button type="button" class="btn-secondary" onclick="previousStep()">
                        <i class="fas fa-arrow-left"></i> Previous
                    </button>
                    <button type="button" class="signup-btn finish-btn" onclick="completeSignup()">
                        <i class="fas fa-check"></i> Complete Setup
                    </button>
                </div>
            `;
            break;
    }
}

// File upload functions
function triggerFileUpload(inputId) {
    document.getElementById(inputId).click();
}

function handleFileUpload(input, inputId) {
    const uploadArea = input.parentNode;
    const uploadContent = uploadArea.querySelector('.upload-content');
    
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const fileName = file.name;
        const fileSize = (file.size / 1024 / 1024).toFixed(2); // Size in MB
        
        uploadContent.innerHTML = `
            <i class="fas fa-check-circle" style="font-size: 24px; color: #00d4aa; margin-bottom: 10px;"></i>
            <p style="color: #00d4aa; font-size: 14px; font-weight: 500;">${fileName}</p>
            <p style="color: #888; font-size: 12px;">${fileSize} MB</p>
        `;
        
        uploadArea.style.borderColor = '#00d4aa';
        uploadArea.style.backgroundColor = 'rgba(0, 212, 170, 0.1)';
    }
}

// Member management functions
function removeMember(button) {
    const memberItem = button.closest('.member-item');
    const input = memberItem.querySelector('input');
    input.value = '';
    input.placeholder = 'Invite member';
    input.removeAttribute('readonly');
    
    button.innerHTML = '<i class="fas fa-plus"></i>';
    button.onclick = () => addMember(button);
    button.classList.remove('remove-member');
    button.classList.add('add-member-btn');
}

function addMember(button = null) {
    const input = button ? button.previousElementSibling : document.getElementById('newMember');
    
    if (input.value.trim()) {
        input.setAttribute('readonly', true);
        
        const actionButton = input.nextElementSibling;
        actionButton.innerHTML = '<i class="fas fa-minus"></i>';
        actionButton.onclick = () => removeMember(actionButton);
        actionButton.classList.remove('add-member-btn');
        actionButton.classList.add('remove-member');
        
        // Add new member slot if less than 5 members
        const membersList = document.querySelector('.members-list');
        const memberCount = membersList.querySelectorAll('.member-item').length;
        
        if (memberCount < 5) {
            const newMemberItem = document.createElement('div');
            newMemberItem.className = 'member-item add-member';
            newMemberItem.innerHTML = `
                <label>Member 0${memberCount + 1}</label>
                <div class="member-input-wrapper">
                    <input type="email" placeholder="Invite member ${memberCount + 1}">
                    <button type="button" class="add-member-btn" onclick="addMember(this)">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
            `;
            membersList.appendChild(newMemberItem);
        }
    }
}

// Complete signup function
function completeSignup() {
    const finishBtn = document.querySelector('.finish-btn');
    const originalText = finishBtn.textContent;
    
    finishBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Completing...';
    finishBtn.disabled = true;
    
    // Final validation and data processing
    setTimeout(() => {
        UserDataFlow.userData.isComplete = true;
        UserDataFlow.saveStepData(5, {});
        
        console.log('Final user data:', UserDataFlow.userData);
        
        // Show success message with summary
        showCompletionModal();
        
        finishBtn.innerHTML = originalText;
        finishBtn.disabled = false;
    }, 2000);
}

function showCompletionModal() {
    const modal = document.createElement('div');
    modal.className = 'completion-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="success-icon">
                <i class="fas fa-check-circle"></i>
            </div>
            <h2>Welcome to Red Aerial Systems!</h2>
            <p>Your account has been successfully created and verified.</p>
            <div class="account-summary">
                <h3>Account Summary:</h3>
                <ul>
                    <li><strong>Name:</strong> ${UserDataFlow.userData.account.name}</li>
                    <li><strong>Email:</strong> ${UserDataFlow.userData.account.email}</li>
                    <li><strong>Role:</strong> ${UserDataFlow.userData.profile.role}</li>
                    <li><strong>Department:</strong> ${UserDataFlow.userData.profile.department}</li>
                    <li><strong>Team Members:</strong> ${UserDataFlow.userData.members.length} invited</li>
                </ul>
            </div>
            <button onclick="closeModal()" class="btn-primary">Get Started</button>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Auto close after 10 seconds
    setTimeout(() => {
        closeModal();
    }, 10000);
}

function closeModal() {
    const modal = document.querySelector('.completion-modal');
    if (modal) {
        modal.remove();
    }
    
    // Clear saved data and reset form
    localStorage.removeItem('redAerialUserData');
    location.reload();
}

function showSuccessMessage(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.innerHTML = `
        <div class="success-content">
            <i class="fas fa-check-circle"></i>
            <p>${message}</p>
        </div>
    `;
    
    const formContainer = document.querySelector('.form-container');
    formContainer.appendChild(successDiv);
    
    setTimeout(() => {
        successDiv.remove();
    }, 3000);
}

// Show sign in form
function showSignIn() {
    const formHeader = document.querySelector('.form-header h1');
    const formDescription = document.querySelector('.form-header p');
    const signupForm = document.querySelector('.signup-form');
    
    formHeader.textContent = 'Welcome Back';
    formDescription.textContent = 'Sign in to your Red Aerial Systems account.';
    
    // Update form for sign in
    signupForm.innerHTML = `
        <button type="button" class="google-btn">
            <img src="https://developers.google.com/identity/images/g-logo.png" alt="Google" class="google-icon">
            Sign In with Google
        </button>

        <div class="divider">
            <span>or</span>
        </div>

        <div class="form-group">
            <label for="loginEmail">Email ID</label>
            <input type="email" id="loginEmail" name="loginEmail" placeholder="Enter your email" required>
        </div>

        <div class="form-group">
            <label for="loginPassword">Password</label>
            <div class="input-wrapper">
                <input type="password" id="loginPassword" name="loginPassword" placeholder="Enter your password" required>
                <span class="toggle-password" onclick="togglePassword('loginPassword')">
                    <i class="fas fa-eye" id="loginPasswordToggle"></i>
                </span>
            </div>
        </div>

        <div class="forgot-password">
            <a href="#" style="color: #00d4aa; text-decoration: none; font-size: 14px;">Forgot Password?</a>
        </div>

        <button type="submit" class="signup-btn">Sign In</button>

        <div class="signin-link">
            <span>Don't have an account? <a href="#" onclick="location.reload()">Sign Up</a></span>
        </div>
    `;
}

// Real-time email validation
document.addEventListener('DOMContentLoaded', function() {
    const emailInput = document.getElementById('email');
    const emailStatus = document.querySelector('.input-status.valid');
    
    if (emailInput) {
        emailInput.addEventListener('input', function() {
            const email = this.value.trim();
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            
            if (emailRegex.test(email)) {
                emailStatus.style.display = 'flex';
                this.style.borderColor = '#00d4aa';
            } else {
                emailStatus.style.display = 'none';
                this.style.borderColor = 'rgba(255, 255, 255, 0.2)';
            }
        });
    }
});

// Google Sign Up functionality
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('google-btn') || e.target.closest('.google-btn')) {
        e.preventDefault();
        alert('Google Sign Up functionality would be implemented here with Google OAuth.');
    }
});

// Step clicking functionality
document.addEventListener('DOMContentLoaded', function() {
    const steps = document.querySelectorAll('.step');
    
    steps.forEach((step, index) => {
        step.addEventListener('click', function() {
            // Remove active class from all steps
            steps.forEach(s => s.classList.remove('active'));
            
            // Add active class to clicked step
            this.classList.add('active');
            
            // Update form content
            updateFormContent(this);
        });
    });
});

// Smooth animations
document.addEventListener('DOMContentLoaded', function() {
    // Add entrance animation to form
    const formContainer = document.querySelector('.form-container');
    formContainer.style.opacity = '0';
    formContainer.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        formContainer.style.transition = 'all 0.6s ease';
        formContainer.style.opacity = '1';
        formContainer.style.transform = 'translateY(0)';
    }, 100);
    
    // Add stagger animation to steps
    const steps = document.querySelectorAll('.step');
    steps.forEach((step, index) => {
        step.style.opacity = '0';
        step.style.transform = 'translateX(-20px)';
        
        setTimeout(() => {
            step.style.transition = 'all 0.4s ease';
            step.style.opacity = '1';
            step.style.transform = 'translateX(0)';
        }, 200 + (index * 100));
    });
}); 