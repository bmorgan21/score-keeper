const modal = new bootstrap.Modal(document.getElementById('modal'))
const dialog = modal._element.querySelector('.modal-dialog');
const defaultModalDialogHTML = dialog.innerHTML;

const modalLinks = document.querySelectorAll('a.ajax-modal');

modalLinks.forEach(link => {
    link.addEventListener('click', evt => {
        evt.preventDefault();

        dialog.innerHTML = defaultModalDialogHTML;

        const url = addQueryParam(evt.target.href, 'modal', '1');

        fetch(url, {
            method: 'GET'
        }).then(response => {
            if (response.ok) {
                response.text().then(data => {
                    dialog.innerHTML = data;
                    bind(dialog);
                });
            }
        });

        modal.show();
    })
});