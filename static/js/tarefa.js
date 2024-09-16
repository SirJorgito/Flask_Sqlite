document.addEventListener('DOMContentLoaded', function() {
    const fileUpload = document.getElementById('arquivo'); // Alterado para o ID correto
    const fileSelectedMsg = document.getElementById('file-selected-msg');
    const fileNameDisplay = document.getElementById('file-name');
    const btnEnviar = document.getElementById('btn_add');
    const customFileUpload = document.querySelector('.custom-file-upload'); // Botão estilizado

    // Simula o clique no input de arquivo quando o botão estilizado for clicado
    customFileUpload.addEventListener('click', function(event) {
        event.preventDefault(); // Previne comportamento padrão
        fileUpload.click();
    });

    // Exibe mensagem quando um arquivo for selecionado
    fileUpload.addEventListener('change', function() {
        const file = fileUpload.files[0]; // Seleciona o primeiro arquivo
        if (file) {
            fileSelectedMsg.style.display = 'block'; // Mostra a mensagem
            fileNameDisplay.textContent = file.name; // Exibe o nome do arquivo
        } else {
            fileSelectedMsg.style.display = 'none'; // Esconde a mensagem
        }
    });

    // Função de envio de arquivo
    btnEnviar.addEventListener('click', function() {
        const file = fileUpload.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const newConteudo = {
                    'id': conteudos.length + 1,
                    'nome': file.name,
                    'tipo': 'arquivo',
                    'link': e.target.result
                };
                conteudos.push(newConteudo); // Adiciona o novo conteúdo à lista
                renderConteudos(); // Re-renderiza a lista com o novo conteúdo
                // Limpa a seleção e esconde a mensagem após o envio
                fileUpload.value = '';
                fileSelectedMsg.style.display = 'none';
            };
            reader.readAsDataURL(file);
        } else {
            alert('Por favor, selecione um arquivo antes de enviar.');
        }
    });
});
