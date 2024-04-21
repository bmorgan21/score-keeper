const bindList = [];

function bind(elem) {
    bindList.forEach(b => {
        b(elem);
    })
}

function addQueryParam(url, key, value) {
    return url + ((url.indexOf('?') == -1) ? "?" : "&") + key + "=" + value;
}

function executeFunctionByName(functionName, context /*, args */) {
    var args = Array.prototype.slice.call(arguments, 2);
    var namespaces = functionName.split(".");
    var func = namespaces.pop();
    for (var i = 0; i < namespaces.length; i++) {
        context = context[namespaces[i]];
    }
    return context[func].apply(context, args);
}

const methodLinks = document.querySelectorAll('a[data-method]');

methodLinks.forEach(link => {
    link.addEventListener('click', evt => {
        evt.preventDefault();

        const callbackFuncName = link.getAttribute('data-callback');

        var fetch_data = {
            method: link.getAttribute('data-method') || 'GET'
        }

        const dataFuncName = link.getAttribute('data-func');
        if (dataFuncName) {
            const result = executeFunctionByName(dataFuncName, window, link);

            fetch_data['body'] = JSON.stringify(result);
            fetch_data['headers'] = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        }

        fetch(link.href, fetch_data).then(response => {
            if (response.ok) {
                response.json().then(data => {
                    if (callbackFuncName) {
                        executeFunctionByName(callbackFuncName, window, link, data);
                    } else {
                        window.location.reload();
                    }
                });
            }
        });
    })
});