import { api, requiredProject } from "./conn.js";

export const NOTIFICATION_INTERVAL = 2500; // ms

export const initNotification = (projectId, success) => {
  var firstTime = true;
  let intervalId = setInterval(() => {
    firstTime = false;
    fetch(api(`/notification?project=${projectId}`))
      .then(async (res) => {
        success(await res.json());
      })
      .catch((err) => {
        console.error(err);
      });
  }, NOTIFICATION_INTERVAL);

  window.addEventListener("beforeunload", () => {
    clearInterval(intervalId);
  });
};

export const getAllNotificationImages = async (notis = null) => {
  try {
    const ids = notis.reduce((acc, curr) => [...acc, curr.img_id], []);
    const response = await fetch(
      api(`/get_snapshot?id=${JSON.stringify(ids)}`)
    );
    const data = await response.json();

    return data;
    console.log(data);
  } catch (e) {
    console.error(e);
  }
};

/**
 * Notifications
 * 1. check if theres project selected /
 * 2. if there is project, continue, else quit /
 * 3. get all notifications from this project -
 * 4. get all images from all notis
 * 4.1 update notification container and html
 * -- advance
 * 5. check for read notis
 * 6. add read icon
 */

export function setupNoti() {
  let after; // use for continous staff

  const icon = document.querySelector(".notification-icon");
  const container = document.querySelector("#notificationPopup");
  container.innerHTML = "";

  icon.onclick = (e) => {
    e.preventDefault();
    container.classList.toggle("show");
  };

  let timeoutId;

  let index = 0;

  requiredProject(async (projectId) => {
    async function loadNotifications() {
      let notifications = [];
      let images = [];
      // get all project notification
      try {
        const path = api(
          "/notification?project=" +
            projectId +
            (after ? `&after=${after}` : "")
        );
        console.log(path);
        const res = await fetch(path);

        if (res.status !== 200) {
          throw new Error(await res.text());
        }

        const data = await res.json();
        notifications = data;

        if (notifications.length > 0) {
          // set after after latest after
          // always assume the last row is the largest value
          after = [...notifications].reverse()[0].id;
        }
      } catch (err) {
        console.error(err);
      }

      // get all images from notis
      try {
        const imageIds = notifications.map((i) => i.img_id);

        const res = await fetch(
          api("/get_snapshot?id=" + JSON.stringify(imageIds))
        );
        if (res.status !== 200) throw new Error(await res.text());

        images = await res.json();
      } catch (err) {
        console.error(err);
      }

      // update html container
      if (notifications.length > 0) {
        // clear previous notifications
        for (const noti of notifications) {
          const imagedata = images.find((i) => i.SSID === noti.img_id);

          const alert = createAlert(
            noti.id,
            "IDK",
            imagedata.SS,
            imagedata.location,
            index + 1
          );

          // container.insertBefore();
          if (container.firstChild) {
            container.insertBefore(alert, container.firstChild);
          } else {
            container.appendChild(alert);
          }

          index++;
        }
      }

      // repeat every NOTIFICATION_INTERVAL
      timeoutId = setTimeout(loadNotifications, NOTIFICATION_INTERVAL);
    }

    window.addEventListener("beforeunload", function () {
      clearTimeout(timeoutId);
    });

    loadNotifications();
  });

  function createAlert(id, type, image, loc, index) {
    let location = {
      lat: null,
      lng: null,
    };
    if (loc) {
      const parsed = JSON.parse(loc);
      location.lat = parsed.lat;
      location.lng = parsed.lng;
    }
    const locString =
      location.lat === null ? "UNKNOWN" : `${location.lat}, ${location.lng}`;

    const alert = document.createElement("div");
    alert.className = "alert";
    alert.dataset.id = id;

    alert.innerHTML = `
        <div class="header">
            <span class="counter">${index}</span>
            <span class="location">${locString}</span>
            <i class="dropdown-icon ph ph-caret-right"></i>
        </div>
        <div class="content">
            <div class="row">
                <span class="label">
                    <i class="ph ph-map-pin"></i> Location:
                </span>
                <span class="value">${locString}</span>
            </div>
            <div class="row">
                <span class="label">
                    <i class="ph ph-bell-simple-ringing"></i> Object Detected
                </span>
                <img class="image" src="data:image/jpeg;base64,${image}" />
            </div>
        </div>
    `;

    alert.onclick = (e) => {
      e.preventDefault();
      alert.classList.toggle("open");
    };

    return alert;
  }
}
