import { api } from "./conn.js";

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

export const registerNotificationHandler = () => {
  // LocalNotifications.addListener(
  //   "localNotificationActionPerformed",
  //   (notiAction) => {
  //     console.log(notiAction);
  //     const notification = notiAction.notification;
  //     if (!notification.extra) {
  //       return;
  //     }
  //     const { projectId, notiId } = notification.extra;
  //     // redirect to project page
  //     window.location.href = `notification.html?project=${projectId}&noti=${notiId}`;
  //   }
  // );
};
