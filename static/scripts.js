async function postData(url = '', data = {}) {
  // Default options are marked with *
  const response = await fetch(url, {
    method: 'POST', // *GET, POST, PUT, DELETE, etc.
    mode: 'cors', // no-cors, *cors, same-origin
    credentials: 'same-origin', // include, *same-origin, omit
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data) // body data type must match "Content-Type" header
  });
  return response.json(); // parses JSON response into native JavaScript objects
}
function numberWithCommas(x) {
  return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}
//aktualizacja salda
let accBalance = document.getElementById('acc-balance')
window.onload = () => {
  fetch("/api/get_bal")
  .then(response => response.json())
  .then(data => {
    accBalance.innerText = numberWithCommas(data.newBalance);
  });
}
//obsluga formularza zakupu
if(document.getElementById('buy-product-form') !== null){
  document.getElementById('buy-product-form').addEventListener('submit', e => {
    e.preventDefault();
    toastr.options = {
      "progressBar": true,
    }
    postData('api/buy_product', 
    {
      name: e.target[0].value,
      price_one: e.target[1].value,
      count: e.target[2].value
    })
    .then(response => {
      if (response.status === 'ok') {
        accBalance.innerText = numberWithCommas(response.newBalance);
        e.target[0].value = '';
        e.target[1].value = '';
        e.target[2].value = '';
        toastr['success']("Udało ci się zakupić produkt/y!")
      } else if (response.status === 'NotEnoughMoney') {
        toastr['error']("Niewystarczające saldo")
      }
    })
  })
}
//obsluga formularza sprzedazy
if(document.getElementById('sell-product-form') !== null){
  document.getElementById('sell-product-form').addEventListener('submit', e => {
    e.preventDefault();
    toastr.options = {
      "progressBar": true,
    }
    postData('api/sell_product', 
    {
      name: e.target[0].value,
      price_one: e.target[1].value,
      count: e.target[2].value
    })
    .then(response => {
      if (response.status === 'ok') {
        accBalance.innerText = numberWithCommas(response.newBalance);
        e.target[0].value = '';
        e.target[1].value = '';
        e.target[2].value = '';
        toastr['success']("Udało ci się sprzedać produkt/y!")
      } else if (response.status === 'NotEnoughStock') {
        toastr['error']("Brak wystarczającej ilości produktów")
      } else if (response.status === 'ItemNotInStock') {
        toastr['error']("Brak podanego przedmiotu w magazynie")
      }
    })
  })
}
//obsluga formularza zmiany salda
if(document.getElementById('change-balance-form') !== null){
  document.getElementById('change-balance-form').addEventListener('submit', e => {
    e.preventDefault();
    toastr.options = {
      "progressBar": true,
    }
    postData('api/change_balance', 
    {
      comment: e.target[0].value,
      value: e.target[1].value,
    })
    .then(response => {
      if (response.status === 'ok') {
        accBalance.innerText = numberWithCommas(response.newBalance);
        e.target[0].value = '';
        e.target[1].value = '';
        toastr['success']("Udało ci się zmienić saldo!")
      } else if (response.status === 'NotEnoughMoney') {
        toastr['error']("Niewystarczające saldo")
      }
    })
  })
}
//sumowanie zamowienia
if(document.getElementsByClassName('calculate-sum')[0] !== undefined) {
  let price = document.getElementById('input-product-price')
  let qty = document.getElementById('input-product-qty')
  document.getElementsByClassName('calculate-sum')[0].addEventListener('input', e => {
    if (e.target !== price && e.target !== qty) {
      return
    }
    document.getElementById('price-sum').innerText = numberWithCommas(price.value * qty.value)
  })
}