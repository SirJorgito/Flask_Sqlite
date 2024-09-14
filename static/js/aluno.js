document.addEventListener('DOMContentLoaded', function() {
    var addClassIcon = document.getElementById('add-class-icon');
    var modal = document.getElementById('addClassModal');
    var closeBtn = document.getElementsByClassName('close')[0];
    var form = document.getElementById('class-code-form');

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

    form.addEventListener('submit', function(event) {
        var classCode = document.getElementById('class-code').value;
        if (!classCode) {
            event.preventDefault(); // Impede o envio do formulário se o código estiver vazio
            alert('Por favor, insira o código da turma.');
        }
    });
});
