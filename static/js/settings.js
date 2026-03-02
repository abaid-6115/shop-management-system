function saveShopSettings() {

    fetch("/update_shop_settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            shop_name: document.getElementById("shop_name").value,
            logo_url: document.getElementById("logo_url").value,
            address: document.getElementById("address").value,
            phone: document.getElementById("phone").value,
            gst_percentage: document.getElementById("gst_percentage").value,
            return_policy: document.getElementById("return_policy").value,
            footer_message: document.getElementById("footer_message").value,
            currency_symbol: document.getElementById("currency_symbol").value
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("Shop Settings Updated Successfully!");
        }
    });
}
function changeEmail() {

    let email = document.getElementById("new_email").value;

    fetch("/update_email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("Email Updated Successfully!");
            location.reload();
        } else {
            alert(data.error);
        }
    });
}


function changePassword() {

    let password = document.getElementById("new_password").value;

    fetch("/update_password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("Password Updated Successfully!");
        } else {
            alert(data.error);
        }
    });
}
function saveSystemSettings() {

    fetch("/update_system_settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            default_low_stock_limit: document.getElementById("default_low_stock_limit").value,
            invoice_prefix: document.getElementById("invoice_prefix").value,
            auto_logout_minutes: document.getElementById("auto_logout_minutes").value,
            show_low_stock_badge: document.getElementById("show_low_stock_badge").checked
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("System Settings Updated Successfully!");
        }
    });
}