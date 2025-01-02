// Function to show the banner popup
function showBannerPopup() {
  document.getElementById("bannerPopup").style.display = "block";
  document.getElementById("overlay").style.display = "block";
}

// Function to close the banner popup
function closeBannerPopup() {
  document.getElementById("bannerPopup").style.display = "none";
  document.getElementById("overlay").style.display = "none";
}

// Automatically show the popup when the page loads
window.onload = function () {
  showBannerPopup();
};
document.addEventListener("DOMContentLoaded", function () {
     const scrollUpButton = document.querySelector('.scroll-up');

     window.addEventListener('scroll', function () {
         if (window.scrollY > 200) {
             scrollUpButton.style.display = 'block';
         } else {
             scrollUpButton.style.display = 'none';
         }
     });

     scrollUpButton.addEventListener('click', function () {
         window.scrollTo({
             top: 0,
             behavior: 'smooth'
         });
     });
 });

 document.addEventListener("DOMContentLoaded", function () {
    function adjustFooter() {
        const content = document.querySelector(".content");
        const footer = document.querySelector(".footer");
        const bodyHeight = document.body.offsetHeight;
        const viewportHeight = window.innerHeight;

        if (bodyHeight < viewportHeight) {
            footer.style.position = "fixed";
            footer.style.bottom = "0";
            footer.style.width = "100%";
        } else {
            footer.style.position = "static";
        }
    }

    // Adjust the footer on page load
    adjustFooter();

    // Re-adjust on window resize
    window.addEventListener("resize", adjustFooter);
});

  //   collapse table
  $(function () {
      $(".fold-table tr.view").on("click", function () {
          if ($(this).hasClass("open")) {
              $(this).removeClass("open").next(".fold").removeClass("open");
          } else {
              $(".fold-table tr.view").removeClass("open").next(".fold").removeClass("open");
              $(this).addClass("open").next(".fold").addClass("open");
          }
      });
  });
