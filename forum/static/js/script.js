document.addEventListener('DOMContentLoaded', function() {
  const menuToggle = document.getElementById('menuToggle');
  const menu = document.getElementById('menu');
  const menuItems = document.querySelectorAll('#menu li');
  menuItems.forEach((item, index) => {
    item.style.setProperty('--item-index', index);
  });

  if (menuToggle && menu) {
    menuToggle.addEventListener('click', function() {
      menu.classList.toggle('show');
    });
  }

  document.addEventListener('click', function(event) {
    if (menu && !menu.contains(event.target) && !menuToggle.contains(event.target) && menu.classList.contains('show')) {
      menu.classList.remove('show');
    }
  });

  window.addEventListener('scroll', function() {
    const header = document.querySelector('header');
    if (header) {
      if (window.scrollY > 50) {
        header.style.padding = '10px 20px';
        header.style.boxShadow = '0 2px 15px rgba(0, 0, 0, 0.2)';
      } else {
        header.style.padding = '15px 20px';
        header.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
      }
    }
  });

  const loginModal = document.getElementById('loginModal');
  const registerModal = document.getElementById('registerModal');
  const loginBtn = document.querySelector('.login-btn');
  const closeBtns = document.querySelectorAll('.close-btn');
  const switchToRegister = document.querySelector('.switch-to-register');
  const switchToLogin = document.querySelector('.switch-to-login');
  const loginForm = document.getElementById('loginForm');

  // Login button click handler
  if (loginBtn) {
    loginBtn.addEventListener('click', function(e) {
      e.preventDefault();
      loginModal.style.display = 'block';
      document.body.style.overflow = 'hidden';
    });
  }

  // Close buttons click handlers
  closeBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      loginModal.style.display = 'none';
      registerModal.style.display = 'none';
      document.body.style.overflow = '';
    });
  });

  // Switch between forms
  if (switchToRegister) {
    switchToRegister.addEventListener('click', function(e) {
      e.preventDefault();
      loginModal.style.display = 'none';
      registerModal.style.display = 'block';
    });
  }

  if (switchToLogin) {
    switchToLogin.addEventListener('click', function(e) {
      e.preventDefault();
      registerModal.style.display = 'none';
      loginModal.style.display = 'block';
    });
  }

  // Close modals when clicking outside
  window.addEventListener('click', function(event) {
    if (event.target === loginModal) {
      loginModal.style.display = 'none';
      document.body.style.overflow = '';
    }
    if (event.target === registerModal) {
      registerModal.style.display = 'none';
      document.body.style.overflow = '';
    }
  });

  // Login form validation and submission
  if (loginForm) {
    const loginEmail = document.getElementById('loginEmail');
    const loginPassword = document.getElementById('loginPassword');
    const verificationCodeGroup = document.querySelector('.verification-code-group');
    const verificationCode = document.getElementById('verificationCode');
    const resendCodeLink = document.querySelector('.resend-code-link');
    const timer = document.querySelector('.timer');
    let timerInterval;

    function startTimer(duration) {
      let timeLeft = duration;
      timer.style.display = 'inline';
      resendCodeLink.style.display = 'none';

      clearInterval(timerInterval);
      timerInterval = setInterval(() => {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        timer.textContent = `(${minutes}:${seconds.toString().padStart(2, '0')})`;

        if (--timeLeft < 0) {
          clearInterval(timerInterval);
          timer.style.display = 'none';
          resendCodeLink.style.display = 'inline';
        }
      }, 1000);
    }

    async function sendVerificationCode(email, password) {
      try {
        const response = await fetch('/login/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
          },
          body: JSON.stringify({
            action: 'send_code',
            email: email,
            password: password
          })
        });

        const data = await response.json();
        if (data.status === 'success') {
          verificationCodeGroup.style.display = 'block';
          startTimer(60); // 1 минута таймер
          setValidationMessage(loginEmail, 'Код подтверждения отправлен на ваш email', true);
        } else {
          setValidationMessage(loginEmail, data.message, false);
        }
      } catch (error) {
        setValidationMessage(loginEmail, 'Произошла ошибка при отправке кода', false);
      }
    }

    async function verifyCode(email, password, code) {
      try {
        const response = await fetch('/login/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
          },
          body: JSON.stringify({
            action: 'verify_code',
            email: email,
            password: password,
            code: code
          })
        });

        const data = await response.json();
        if (data.status === 'success') {
          // Показываем сообщение об успешном входе
          const messagesContainer = document.querySelector('.messages');
          if (!messagesContainer) {
            // Если контейнер для сообщений не существует, создаем его
            const newMessagesContainer = document.createElement('div');
            newMessagesContainer.className = 'messages';
            document.querySelector('header').insertAdjacentElement('afterend', newMessagesContainer);
          }
          
          // Создаем и добавляем сообщение
          const messageDiv = document.createElement('div');
          messageDiv.className = 'alert success';
          messageDiv.textContent = data.message;
          document.querySelector('.messages').appendChild(messageDiv);
          
          // Закрываем модальное окно
          loginModal.style.display = 'none';
          document.body.style.overflow = '';
          
          // Перезагружаем страницу через небольшую задержку
          setTimeout(() => {
            window.location.reload();
          }, 1500);
        } else {
          setValidationMessage(verificationCode, data.message, false);
        }
      } catch (error) {
        setValidationMessage(verificationCode, 'Произошла ошибка при проверке кода', false);
      }
    }

    loginEmail.addEventListener('input', function() {
      if (this.value.trim() === '') {
        setValidationMessage(this, 'Email обязателен', false);
      } else if (!isValidEmail(this.value)) {
        setValidationMessage(this, 'Введите корректный email', false);
      } else {
        setValidationMessage(this, '', true);
      }
    });

    loginPassword.addEventListener('input', function() {
      if (this.value.trim() === '') {
        setValidationMessage(this, 'Пароль обязателен', false);
      } else {
        setValidationMessage(this, '', true);
      }
    });

    verificationCode.addEventListener('input', function() {
      this.value = this.value.replace(/\D/g, '').slice(0, 6);
      if (this.value.length === 6) {
        verifyCode(loginEmail.value, loginPassword.value, this.value);
      }
    });

    resendCodeLink.addEventListener('click', function(e) {
      e.preventDefault();
      sendVerificationCode(loginEmail.value, loginPassword.value);
    });

    loginForm.addEventListener('submit', function(e) {
      e.preventDefault();
      let isFormValid = true;

      if (loginEmail.value.trim() === '' || !isValidEmail(loginEmail.value)) {
        setValidationMessage(loginEmail, 'Введите корректный email', false);
        isFormValid = false;
      }

      if (loginPassword.value.trim() === '') {
        setValidationMessage(loginPassword, 'Введите пароль', false);
        isFormValid = false;
      }

      if (isFormValid) {
        if (!verificationCodeGroup.style.display || verificationCodeGroup.style.display === 'none') {
          sendVerificationCode(loginEmail.value, loginPassword.value);
        } else if (verificationCode.value.length === 6) {
          verifyCode(loginEmail.value, loginPassword.value, verificationCode.value);
        } else {
          setValidationMessage(verificationCode, 'Введите код подтверждения', false);
        }
      } else {
        loginForm.classList.add('shake');
        setTimeout(() => {
          loginForm.classList.remove('shake');
        }, 500);
      }
    });
  }

  const registerBtns = document.querySelectorAll('.register-btn');
  const registerForm = document.getElementById('registerForm');

  registerBtns.forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      registerModal.style.display = 'block';
      document.body.style.overflow = 'hidden';
    });
  });

  if (registerForm) {
    const firstName = document.getElementById('firstName');
    const lastName = document.getElementById('lastName');
    const email = document.getElementById('email');
    const phone = document.getElementById('phone');
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirmPassword');
    const bio = document.getElementById('bio');
    const agree = document.getElementById('agree');


    const formInputs = registerForm.querySelectorAll('input:not([type="checkbox"]), textarea');
    formInputs.forEach(input => {
      if (!input.hasAttribute('placeholder')) {
        input.setAttribute('placeholder', ' ');
      }
    });

    firstName.addEventListener('input', function() {
      validateName(this, 'имени');
    });

    lastName.addEventListener('input', function() {
      validateName(this, 'фамилии');
    });

    email.addEventListener('input', function() {
      const messageElement = this.nextElementSibling;
      if (this.value.trim() === '') {
        setValidationMessage(this, 'Email обязателен', false);
      } else if (!isValidEmail(this.value)) {
        setValidationMessage(this, 'Введите корректный email', false);
      } else {
        setValidationMessage(this, 'Email корректен', true);
      }
    });

    phone.addEventListener('input', function() {
      this.value = formatPhoneNumber(this.value);

      if (this.value.trim() === '') {
        setValidationMessage(this, 'Телефон обязателен', false);
      } else if (!isValidPhone(this.value)) {
        setValidationMessage(this, 'Введите корректный телефон', false);
      } else {
        setValidationMessage(this, 'Телефон корректен', true);
      }
    });

    password.addEventListener('input', function() {
      if (this.value.trim() === '') {
        setValidationMessage(this, 'Пароль обязателен', false);
      } else if (this.value.length < 8) {
        setValidationMessage(this, 'Пароль должен содержать минимум 8 символов', false);
      } else if (!isStrongPassword(this.value)) {
        setValidationMessage(this, 'Пароль должен содержать буквы, цифры и специальные символы', false);
      } else {
        setValidationMessage(this, 'Пароль корректен', true);
      }

      if (confirmPassword.value) {
        validatePasswordMatch();
      }
    });

    confirmPassword.addEventListener('input', function() {
      validatePasswordMatch();
    });

    bio.addEventListener('input', function() {
      const remaining = 200 - this.value.length;
      setValidationMessage(this, `Осталось символов: ${remaining}`, true);
    });

    registerForm.addEventListener('submit', function(e) {
      let isFormValid = true;

      isFormValid = validateName(firstName, 'имени') && isFormValid;
      isFormValid = validateName(lastName, 'фамилии') && isFormValid;

      if (email.value.trim() === '' || !isValidEmail(email.value)) {
        setValidationMessage(email, 'Введите корректный email', false);
        isFormValid = false;
      }

      if (phone.value.trim() === '' || !isValidPhone(phone.value)) {
        setValidationMessage(phone, 'Введите корректный телефон', false);
        isFormValid = false;
      }

      if (password.value.trim() === '' || password.value.length < 8 || !isStrongPassword(password.value)) {
        setValidationMessage(password, 'Введите корректный пароль', false);
        isFormValid = false;
      }

      if (password.value !== confirmPassword.value) {
        setValidationMessage(confirmPassword, 'Пароли не совпадают', false);
        isFormValid = false;
      }

      if (!agree.checked) {
        const agreeMessageElement = agree.parentElement.nextElementSibling;
        agreeMessageElement.textContent = 'Необходимо согласие с правилами';
        isFormValid = false;
      } else {
        const agreeMessageElement = agree.parentElement.nextElementSibling;
        agreeMessageElement.textContent = '';
      }

      if (isFormValid) {
        return true;
      } else {
        e.preventDefault(); 
        registerForm.classList.add('shake');
        setTimeout(() => {
          registerForm.classList.remove('shake');
        }, 500);
      }
    });

    function validateName(input, fieldName) {
      const value = input.value.trim();
      const messageElement = input.nextElementSibling;

      if (value === '') {
        setValidationMessage(input, `Поле ${fieldName} обязательно`, false);
        return false;
      }

      if (!/^[А-Яа-яA-Za-z]+$/.test(value)) {
        setValidationMessage(input, `Поле ${fieldName} должно содержать только буквы`, false);
        return false;
      }

      if (!/^[А-ЯA-Z][а-яa-z]*$/.test(value)) {
        setValidationMessage(input, `В поле ${fieldName} только первая буква должна быть заглавной`, false);
        return false;
      }

      setValidationMessage(input, `Поле ${fieldName} заполнено корректно`, true);
      return true;
    }

    function validatePasswordMatch() {
      if (confirmPassword.value.trim() === '') {
        setValidationMessage(confirmPassword, 'Подтверждение пароля обязательно', false);
      } else if (password.value !== confirmPassword.value) {
        setValidationMessage(confirmPassword, 'Пароли не совпадают', false);
      } else {
        setValidationMessage(confirmPassword, 'Пароли совпадают', true);
      }
    }

    function setValidationMessage(input, message, isValid) {
      const messageElement = input.nextElementSibling;
      messageElement.textContent = message;

      if (isValid) {
        messageElement.parentElement.classList.add('validation-success');
      } else {
        messageElement.parentElement.classList.remove('validation-success');
      }
    }

    function isValidEmail(email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(email);
    }

    function isValidPhone(phone) {
      const cleanPhone = phone.replace(/\D/g, '');
      return cleanPhone.length >= 10 && cleanPhone.length <= 15;
    }

    function formatPhoneNumber(phone) {
      let cleaned = phone.replace(/\D/g, '');

      cleaned = cleaned.substring(0, 15);

      let formatted = '';

      if (cleaned.length > 0) {
        formatted = '+' + cleaned.substring(0, 1);

        if (cleaned.length > 1) {
          formatted += ' (' + cleaned.substring(1, 4);

          if (cleaned.length > 4) {
            formatted += ') ' + cleaned.substring(4, 7);

            if (cleaned.length > 7) {
              formatted += '-' + cleaned.substring(7, 9);

              if (cleaned.length > 9) {
                formatted += '-' + cleaned.substring(9);
              }
            }
          }
        }
      }

      return formatted;
    }

    function isStrongPassword(password) {
      const hasLetter = /[a-zA-Zа-яА-Я]/.test(password);
      const hasDigit = /\d/.test(password);
      const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);

      return hasLetter && hasDigit && hasSpecial;
    }
  }

  // Функция для показа уведомлений
  function showNotification(type, title, message) {
    // Удаляем предыдущие уведомления
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
      existingNotification.remove();
    }

    // Создаем новое уведомление
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Иконка в зависимости от типа уведомления
    const iconSvg = type === 'success' 
      ? '<svg class="notification-icon success" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>'
      : '<svg class="notification-icon error" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>';

    notification.innerHTML = `
      ${iconSvg}
      <div class="notification-content">
        <div class="notification-title">${title}</div>
        <div class="notification-message">${message}</div>
      </div>
      <div class="notification-close">&times;</div>
    `;

    // Добавляем уведомление на страницу
    document.body.appendChild(notification);

    // Показываем уведомление с анимацией
    setTimeout(() => notification.classList.add('show'), 10);

    // Добавляем обработчик для кнопки закрытия
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
      notification.classList.remove('show');
      setTimeout(() => notification.remove(), 300);
    });

    // Автоматически скрываем уведомление через 5 секунд
    setTimeout(() => {
      if (notification.parentElement) {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
      }
    }, 5000);
  }

  // Обработка формы обратной связи
  const contactForm = document.getElementById('contactForm');
  if (contactForm) {
    contactForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      // Получаем данные формы
      const formData = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        subject: document.getElementById('subject').value,
        message: document.getElementById('message').value
      };

      // Проверяем заполнение всех полей
      if (!formData.name || !formData.email || !formData.subject || !formData.message) {
        showNotification('error', 'Ошибка', 'Пожалуйста, заполните все поля формы');
        return;
      }

      // Показываем индикатор загрузки
      const submitButton = contactForm.querySelector('button[type="submit"]');
      const originalButtonText = submitButton.textContent;
      submitButton.textContent = 'Отправка...';
      submitButton.disabled = true;

      try {
        const response = await fetch('/send_message/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
          },
          body: JSON.stringify(formData)
        });

        const result = await response.json();
        
        if (result.status === 'success') {
          showNotification(
            'success',
            'Сообщение отправлено',
            'Спасибо за обращение! Мы свяжемся с вами в ближайшее время.'
          );
          contactForm.reset();
        } else {
          showNotification(
            'error',
            'Ошибка отправки',
            'Произошла ошибка при отправке сообщения. Пожалуйста, попробуйте позже.'
          );
        }
      } catch (error) {
        showNotification(
          'error',
          'Ошибка отправки',
          'Произошла ошибка при отправке сообщения. Пожалуйста, попробуйте позже.'
        );
        console.error('Error:', error);
      } finally {
        // Восстанавливаем кнопку
        submitButton.textContent = originalButtonText;
        submitButton.disabled = false;
      }
    });
  }
});
