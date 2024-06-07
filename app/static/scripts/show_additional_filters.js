"use strict"

window.onload = function () {
    let additionalFilters = document.getElementById("additionalFilters");

    let additionalFiltersShown = false;

    let showAdditionalFiltersBtn = document.getElementById("showAdditionalFilters");
    showAdditionalFiltersBtn.onclick = function () {
        if (additionalFiltersShown) {
            additionalFilters.classList.add("hidden");
            additionalFiltersShown = false;
        } else {
            additionalFilters.classList.remove("hidden");
            additionalFiltersShown = true;
        }
        console.log(additionalFiltersShown);
    }
}