document.addEventListener('DOMContentLoaded', function() {
    var addClassIcon = document.getElementById('add-class-icon');
    var modal = document.getElementById('addClassModal');
    var closeBtn = document.getElementsByClassName('close')[0];

    addClassIcon.addEventListener('click', function() {
        modal.style.display = 'block';
    });

    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    });
});
