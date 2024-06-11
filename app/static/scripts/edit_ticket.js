"use strict"

let amount;
let old_price;
let new_price;
let price_per_person;
let editTicketBtn;

function calculatePrice() {
    let total_price =  price_per_person * amount.value;
    new_price.innerHTML = total_price;
    editTicketBtn.innerHTML = `Изменить билет за ${total_price - old_price} &#8381;`;
}

window.onload = function () {
    amount = document.getElementById("amount");
    old_price = document.getElementById("old_price").innerText;
    price_per_person = old_price / amount.value;
    new_price = document.getElementById("new_price");
    editTicketBtn = document.getElementById("editTicketBtn");

    amount.oninput = calculatePrice;
    calculatePrice();

    let deleteModal = document.getElementById("delete-modal");
    deleteModal.addEventListener("show.bs.modal", fillModal);
}