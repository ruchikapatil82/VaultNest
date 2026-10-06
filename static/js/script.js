// --------------------------------------------------
// SHOW / HIDE SAVED PASSWORD
// --------------------------------------------------

function togglePassword(id, password, button) {

    const element =
        document.getElementById("password-" + id);

    if (element.innerText === "••••••••") {

        element.innerText = password;
        button.innerText = "Hide";

    } else {

        element.innerText = "••••••••";
        button.innerText = "Show";

    }
}


// --------------------------------------------------
// SHOW / HIDE INPUT PASSWORD
// --------------------------------------------------

function toggleInputPassword() {

    const passwordInput =
        document.getElementById("password");

    if (passwordInput.type === "password") {

        passwordInput.type = "text";

    } else {

        passwordInput.type = "password";

    }
}


// --------------------------------------------------
// COPY PASSWORD
// --------------------------------------------------

function copyPassword(password) {

    navigator.clipboard.writeText(password)
        .then(function() {

            alert("Password copied to clipboard.");

        })
        .catch(function() {

            alert("Unable to copy password.");

        });
}


// --------------------------------------------------
// SEARCH PASSWORDS
// --------------------------------------------------

function searchPasswords() {

    const searchInput =
        document.getElementById("searchInput");

    const searchText =
        searchInput.value.toLowerCase();

    const cards =
        document.querySelectorAll(".password-card");

    cards.forEach(function(card) {

        const website =
            card.getAttribute("data-search");

        if (website.includes(searchText)) {

            card.style.display = "block";

        } else {

            card.style.display = "none";

        }

    });
}


// --------------------------------------------------
// GENERATE PASSWORD
// --------------------------------------------------

function generatePassword() {

    fetch("/generate-password")

        .then(response => response.json())

        .then(data => {

            document.getElementById("password").value =
                data.password;

            document.getElementById("password").type =
                "text";

        })

        .catch(error => {

            console.log(error);

            alert("Unable to generate password.");

        });
}