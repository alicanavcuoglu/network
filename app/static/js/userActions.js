// Send a message to a friend
document.querySelectorAll(".msg-btn").forEach((msgBtn) => {
  const username = msgBtn.closest(".list-group-item").getAttribute("data-user-username");

  msgBtn.addEventListener("click", function(e) {
    e.preventDefault();

    fetch("url_for('main.')")
  })
});

// Add a user as a friend
document.querySelectorAll(".add-btn").forEach((addBtn) => {
  const username = addBtn
    .closest(".list-group-item")
    .getAttribute("data-user-username");

  addBtn.addEventListener("click", (e) => {
    e.preventDefault();

    fetch(`/requests/${username}`, {
      method: "POST",
    })
      .then((response) => {
        if (response.ok) {
          location.reload();
        }
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  });
});

// Accept a friendship request
document.querySelectorAll(".accept-btn").forEach((acceptBtn) => {
  const username = acceptBtn
    .closest(".list-group-item")
    .getAttribute("data-user-username");

  acceptBtn.addEventListener("click", (e) => {
    e.preventDefault();

    fetch(`/requests/${username}/accept`, {
      method: "POST",
    })
      .then((response) => {
        if (response.ok) {
          location.reload();
        }
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  });
});


// Decline a friendship request
document.querySelectorAll(".decline-btn").forEach((declineBtn) => {
  const username = declineBtn
    .closest(".list-group-item")
    .getAttribute("data-user-username");

  declineBtn.addEventListener("click", (e) => {
    e.preventDefault();

    fetch(`/requests/${username}/decline`, {
      method: "POST",
    })
      .then((response) => {
        if (response.ok) {
          location.reload();
        }
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  });
});


// Remove a user from friends
document.querySelectorAll(".remove-btn").forEach((removeBtn) => {
  const username = removeBtn
    .closest(".modal")
    .getAttribute("data-user-username");

  removeBtn.addEventListener("click", (e) => {
    fetch(`/friends/${username}/remove`, {
      method: "DELETE",
    })
      .then((response) => {
        if (response.ok) {
          location.reload();
        }
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  });
});