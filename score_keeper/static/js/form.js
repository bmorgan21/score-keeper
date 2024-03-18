function clearValidation(form) {
    const errorMsgs = form.querySelectorAll('.invalid-feedback');
    errorMsgs.forEach((e) => e.remove());

    const inputs = form.querySelectorAll('input.is-invalid');
    inputs.forEach((e) => e.classList.remove('is-invalid'));
}

function startLoading(form) {
    form.classList.add('loading');
    const spinners = form.querySelectorAll('.loading-spinner');
    spinners.forEach((e) => e.classList.remove('d-none'));
    Array.from(form.elements).forEach((element) => {
        if (!element.disabled) {
            element.classList.add('x-form-disabled');
            element.disabled = true;
        }
    });
}

function stopLoading(form) {
    form.classList.remove('loading');
    const spinners = form.querySelectorAll('.loading-spinner');
    spinners.forEach((e) => e.classList.add('d-none'));
    Array.from(form.elements).forEach((element) => {
        if (element.classList.contains('x-form-disabled')) {
            element.classList.remove('x-form-disabled')
            element.disabled = false;
        }
    });
}

function nodeCallback(node) {
    if (node.classList && node.classList.contains('input')) {
        const isPlaceholder = node.classList.contains('input-placeholder');
        const value = node.innerText;
        return { name: node.getAttribute('id'), value: isPlaceholder ? '' : value }
    }
    return null;
}

function defaultFormCallback(form, data) {
    const status = form.querySelector('.status');
    const rInput = form.querySelector('input[name="r"]');
    let target = form.target;
    if (!target) {
        target = '_self';
    }

    if (rInput && rInput.value) {
        const regex = /%7B-.*?-%7D/g;
        let url = rInput.value.replace('{ID}', data['id']);
        let matches = url.match(regex);
        if (matches) {
            matches.forEach(s => {
                url = url.replace(s, data[s.substring(4, s.length - 4)])
            });
        }

        if (target == '_top') {
            window.location.replace(url);
        } else {
            const modal = form.closest('.modal');
            if (modal) {
                fetch(url, {
                    method: 'GET'
                }).then(response => {
                    if (response.ok) {
                        response.text().then(data => {
                            const dialog = modal.querySelector('.modal-dialog');
                            dialog.innerHTML = data;
                            bind(dialog);
                        });
                    }
                });
            } else {
                window.location.replace(url);
            }
        }
    } else {
        if (target == '_top') {
            window.location.reload();
        } else {
            stopLoading(form);
            clearValidation(form);
            if (status) {
                status.innerHTML = "Thanks for your submission!";
            }
            form.reset()
        }
    }
}

async function handleSubmit(event, callback) {
    event.preventDefault();

    const form = event.target;
    const status = form.querySelector('.status');
    const data = form2js(form, '.', false, nodeCallback);

    startLoading(form);

    fetch(form.action, {
        method: form.getAttribute("method"),
        body: JSON.stringify(data),
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    }).then(response => {
        if (response.ok) {
            response.json().then(data => {
                callback(form, data);
            });
        } else if (response.status == 500) {
            stopLoading(form);
            if (status) {
                status.innerHTML = "Oops! There was a problem submitting your form"
            }
        } else {
            stopLoading(form);
            clearValidation(form);
            response.json().then(data => {
                if (Object.hasOwn(data, 'errors')) {
                    const ul = document.createElement('ul');
                    data.errors.forEach((value) => {
                        const input = form.querySelector('[name="' + value.loc + '"]');
                        if (input) {
                            input.classList.add('is-invalid');

                            const div = input.parentElement;
                            const error = document.createElement('div');
                            error.classList.add('invalid-feedback');
                            error.innerHTML = value.msg;
                            div.appendChild(error);
                        } else {
                            const element = document.getElementById(value.loc);
                            if (element) {
                                const error = document.createElement('div');
                                error.classList.add('invalid-feedback');
                                error.classList.add('d-block');
                                error.innerHTML = '<i class="bi bi-exclamation-triangle-fill"></i> ' + value.msg;

                                if (element.classList.contains('input')) {
                                    const div = element.parentElement;
                                    div.appendChild(error);
                                } else {
                                    element.appendChild(error);
                                }
                            } else {
                                const li = document.createElement('li');
                                if (value.loc != '') {
                                    li.innerHTML = "[" + value.loc + "] " + value.msg;
                                } else {
                                    li.innerHTML = value.msg;
                                }
                                ul.appendChild(li)
                            }
                        }
                    });

                    if (status) {
                        status.innerHTML = "Correct the errors above.";
                        if (ul.children.length > 0) {
                            status.appendChild(ul);
                        }
                    }
                } else {
                    if (status) {
                        status.innerHTML = "Oops! There was a problem submitting your form"
                    }
                }
            })
        }
    }).catch(error => {
        stopLoading(form);
        console.log(error);
        if (status) {
            status.innerHTML = "Oops! There was a problem submitting your form"
        }
    });
}

function ajaxFormBind(elem) {
    const forms = elem.querySelectorAll('form.ajax');

    forms.forEach(form => form.addEventListener('submit', event => { handleSubmit(event, defaultFormCallback) }));
}

if (bindList) {
    bindList.push(ajaxFormBind);
}

ajaxFormBind(document);