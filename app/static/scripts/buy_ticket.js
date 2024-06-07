"use strict"

function calculatePrice() {
    let total_price = price.innerText * amount.value;

    buyTicketBtn.innerHTML = `Купить билет за ${total_price} &#8381;`
}

window.onload = function () {
    let amount = document.getElementById("amount");
    let price = document.getElementById("price");
    let buyTicketBtn = document.getElementById("buyTicketBtn");

    amount.oninput = calculatePrice;
    calculatePrice();
}