
var LAST_RESULT = undefined

function documentReady(fn) {
    if (document.readyState === "complete" || document.readyState === "interactive") {
        setTimeout(fn, 1);
    } else {
        document.addEventListener("DOMContentLoaded", fn);
    }
}

function setStatusText(text) {
    var resultStatusContainer = document.getElementById('qr-reader-results-status')
    resultStatusContainer.innerHTML = text
}

function setDetailText(text) {
    var resultDetailContainer = document.getElementById('qr-reader-results-detail');
    resultDetailContainer.innerHTML = text
}

function setDataText(text) {
    var resultDataContainer = document.getElementById('qr-reader-results-data');
    resultDataContainer.innerHTML = text
}

function parseResponse(response) {
    return {
        verified: response.status === "ok",
        detail: response.detail,
        data: response.data,
    }
}

async function postSignature(decodedText) {
    const response = await fetch("/api/pass/verify", {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: (decodedText)
    });
    return await response.json();
}

function displayResponse(verified, detail, data) {
    if (verified) {
        setStatusText("Validierung erfolgreich")
    } else {
        setStatusText("Validierung fehlgeschlagen")
    }

    setDetailText(detail)
    setDataText(data)
}

function parseSignature(rawSignature) {
    return rawSignature.replace(/'/g, '"')
}

function onScanSuccess(decodedSignature, _) {
    if (decodedSignature === LAST_RESULT) {
        return
    }

    LAST_RESULT = decodedSignature

    postSignature(parseSignature(LAST_RESULT)).then((response) => {
        const { verified, detail, data } = parseResponse(response)
        displayResponse(verified, detail, data)
    });
}

documentReady(() => {
    var html5QrcodeScanner = new Html5QrcodeScanner(
        "qr-reader", { fps: 2, qrbox: 400 });

    html5QrcodeScanner.render(onScanSuccess);
});
