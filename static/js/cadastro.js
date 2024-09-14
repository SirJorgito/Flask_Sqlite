document.getElementById('show-aluno').addEventListener('click', function() {
    document.getElementById('aluno-form').style.display = 'block';
    document.getElementById('professor-form').style.display = 'none';
});

document.getElementById('show-professor').addEventListener('click', function() {
    document.getElementById('aluno-form').style.display = 'none';
    document.getElementById('professor-form').style.display = 'block';
});
