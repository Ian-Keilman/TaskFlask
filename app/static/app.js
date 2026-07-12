document.addEventListener("submit", (event) => {
    const message = event.target.dataset.confirm;

    if (message && !window.confirm(message)) {
        event.preventDefault();
    }
});

const board = document.querySelector("[data-task-board]");

if (board) {
    let draggedCard = null;
    const statusMessage = document.querySelector(".drag-status");

    board.addEventListener("dragstart", (event) => {
        const card = event.target.closest("[data-task-id]");
        if (!card) return;

        draggedCard = card;
        card.classList.add("is-dragging");
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", card.dataset.taskId);
    });

    board.addEventListener("dragend", () => {
        draggedCard?.classList.remove("is-dragging");
        board.querySelectorAll(".is-drag-over").forEach((column) => column.classList.remove("is-drag-over"));
        draggedCard = null;
    });

    board.addEventListener("dragover", (event) => {
        const column = event.target.closest("[data-status]");
        if (!column || !draggedCard) return;

        event.preventDefault();
        event.dataTransfer.dropEffect = "move";
        board.querySelectorAll(".is-drag-over").forEach((item) => item.classList.remove("is-drag-over"));
        column.classList.add("is-drag-over");
    });

    board.addEventListener("drop", async (event) => {
        const column = event.target.closest("[data-status]");
        if (!column || !draggedCard) return;

        event.preventDefault();
        const newStatus = column.dataset.status;
        const currentColumn = draggedCard.closest("[data-status]");

        if (currentColumn?.dataset.status === newStatus) return;

        const formData = new FormData();
        formData.set("status", newStatus);
        draggedCard.classList.add("is-updating");

        try {
            const response = await fetch(draggedCard.dataset.statusUrl, {
                method: "POST",
                body: formData,
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });

            if (!response.ok) throw new Error("Status update failed");

            statusMessage.textContent = `Task moved to ${newStatus}.`;
            window.location.reload();
        } catch (error) {
            draggedCard.classList.remove("is-updating");
            statusMessage.textContent = "The task could not be moved. Please use the status menu on the card.";
            window.alert(statusMessage.textContent);
        }
    });
}
