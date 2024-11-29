// Add a user as a friend
document.querySelectorAll('.add-btn').forEach((addBtn) => {
  const username = addBtn.getAttribute('data-user-username');

  addBtn.addEventListener('click', (e) => {
    e.preventDefault();

    fetch(`/requests/${username}`, {
      method: 'POST',
    })
      .then((response) => {
        if (response.ok) {
          location.reload();
        }
      })
      .catch((error) => {
        console.error('Error:', error);
      });
  });
});

// Accept a friendship request
document.querySelectorAll('.accept-btn').forEach((acceptBtn) => {
  const username = acceptBtn.getAttribute('data-user-username');

  acceptBtn.addEventListener('click', (e) => {
    e.preventDefault();

    fetch(`/requests/${username}/accept`, {
      method: 'POST',
    })
      .then((response) => {
        if (response.ok) {
          location.reload();
        }
      })
      .catch((error) => {
        console.error('Error:', error);
      });
  });
});

// Decline a friendship request
document.querySelectorAll('.decline-btn').forEach((declineBtn) => {
  const username = declineBtn.getAttribute('data-user-username');

  declineBtn.addEventListener('click', (e) => {
    e.preventDefault();

    fetch(`/requests/${username}/decline`, {
      method: 'POST',
    })
      .then((response) => {
        if (response.ok) {
          location.reload();
        }
      })
      .catch((error) => {
        console.error('Error:', error);
      });
  });
});

// Remove a user from friends
document.querySelectorAll('.remove-btn').forEach((removeBtn) => {
  const username = removeBtn
    .closest('.modal')
    .getAttribute('data-user-username');

  removeBtn.addEventListener('click', (e) => {
    fetch(`/friends/${username}/remove`, {
      method: 'DELETE',
    })
      .then((response) => {
        if (response.ok) {
          location.reload();
        }
      })
      .catch((error) => {
        console.error('Error:', error);
      });
  });
});

// Invite a user to group
document.querySelectorAll('.invite-btn').forEach((inviteBtn) => {
  const userId = inviteBtn.getAttribute('data-user-id');
  const groupId = inviteBtn.getAttribute('data-group-id');

  inviteBtn.addEventListener('click', (e) => {
    e.preventDefault();

    fetch(`/groups/${groupId}/invite`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userId),
    })
      .then((response) => response.json())
      .then((data) => {
        // If error throw error to display flash
        if (data.error) {
          throw new Error(data.error);
        }

        const inviteBtn = document.querySelector(`[data-user-id="${userId}"]`);
        inviteBtn.disabled = true;
        inviteBtn.textContent = 'Invited';
      })
      .catch((error) => {
        window.location.reload();
        console.error('Error:', error);
      });
  });
});

// Redirect to message page
function redirectToMsg(username) {
  event.preventDefault();

  window.location.href = `/messages/${username}`;
}

// Make admin
function makeAdmin(id, userId) {
  fetch(`/groups/${id}/make-admin/${userId}`, {
    method: 'POST',
  })
    .then((response) => {
      if (response.ok) {
        window.location.reload();
      }
    })
    .catch((error) => console.error(error));
}

// Revoke admin
function revokeAdmin(id, userId) {
  fetch(`/groups/${id}/revoke-admin/${userId}`, {
    method: 'POST',
  })
    .then((response) => {
      if (response.ok) {
        window.location.reload();
      }
    })
    .catch((error) => console.error(error));
}

// Remove a user from group
function removeUserFromGroup(id, userId) {
  fetch(`/groups/${id}/remove-user/${userId}`, {
    method: 'POST',
  })
    .then((response) => {
      if (response.ok) {
        window.location.reload();
      }
    })
    .catch((error) => {
      console.error('Error:', error);
    });
}
