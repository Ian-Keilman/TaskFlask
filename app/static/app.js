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

const burnupChart = document.querySelector("[data-burnup-chart]");

if (burnupChart) {
    const dataElement = burnupChart.querySelector("[data-burnup-data]");

    if (dataElement) {
        const sprints = JSON.parse(dataElement.textContent);
        const select = burnupChart.querySelector("[data-burnup-select]");
        const svg = burnupChart.querySelector("[data-burnup-svg]");
        const emptyState = burnupChart.querySelector("[data-burnup-empty]");
        const completedValue = burnupChart.querySelector("[data-burnup-completed]");
        const totalValue = burnupChart.querySelector("[data-burnup-total]");
        const percentValue = burnupChart.querySelector("[data-burnup-percent]");
        const boardLink = burnupChart.querySelector("[data-burnup-link]");
        const description = burnupChart.querySelector("[data-burnup-description]");
        const svgNamespace = "http://www.w3.org/2000/svg";

        const createSvgElement = (name, attributes = {}) => {
            const element = document.createElementNS(svgNamespace, name);
            Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
            return element;
        };

        const formatChartDate = (value) => {
            const date = new Date(`${value}T00:00:00Z`);
            return new Intl.DateTimeFormat("en-US", {
                month: "short",
                day: "numeric",
                timeZone: "UTC",
            }).format(date);
        };

        const renderBurnup = (sprint) => {
            completedValue.textContent = `${sprint.completed_points} SP`;
            totalValue.textContent = `${sprint.total_points} SP`;
            percentValue.textContent = `${sprint.percent_complete}%`;
            boardLink.href = sprint.board_url;
            svg.setAttribute("aria-label", `${sprint.name} burnup chart`);
            description.textContent = `${sprint.name}: ${sprint.completed_points} of ${sprint.total_points} story points completed.`;

            if (!sprint.total_points) {
                svg.hidden = true;
                emptyState.hidden = false;
                return;
            }

            svg.hidden = false;
            emptyState.hidden = true;
            svg.replaceChildren();

            const width = 800;
            const height = 300;
            const padding = { top: 20, right: 22, bottom: 42, left: 54 };
            const plotWidth = width - padding.left - padding.right;
            const plotHeight = height - padding.top - padding.bottom;
            const maxPoints = Math.max(sprint.total_points, 1);
            const pointCount = sprint.points.length;
            const xPosition = (index) => pointCount === 1
                ? padding.left + plotWidth / 2
                : padding.left + (index / (pointCount - 1)) * plotWidth;
            const yPosition = (value) => padding.top + plotHeight - (value / maxPoints) * plotHeight;

            for (let step = 0; step <= 4; step += 1) {
                const value = Math.round((maxPoints / 4) * step);
                const y = yPosition(value);
                svg.appendChild(createSvgElement("line", {
                    class: "burnup-grid-line",
                    x1: padding.left,
                    x2: width - padding.right,
                    y1: y,
                    y2: y,
                }));

                const label = createSvgElement("text", {
                    class: "burnup-axis-label",
                    x: padding.left - 10,
                    y: y + 4,
                    "text-anchor": "end",
                });
                label.textContent = value;
                svg.appendChild(label);
            }

            const labelIndexes = [...new Set([0, Math.floor((pointCount - 1) / 2), pointCount - 1])];
            labelIndexes.forEach((index) => {
                const label = createSvgElement("text", {
                    class: "burnup-axis-label",
                    x: xPosition(index),
                    y: height - 14,
                    "text-anchor": index === 0 ? "start" : index === pointCount - 1 ? "end" : "middle",
                });
                label.textContent = formatChartDate(sprint.points[index].date);
                svg.appendChild(label);
            });

            const totalPoints = sprint.points
                .map((point, index) => `${xPosition(index)},${yPosition(point.total)}`)
                .join(" ");
            const completedPoints = sprint.points
                .map((point, index) => `${xPosition(index)},${yPosition(point.completed)}`)
                .join(" ");

            svg.appendChild(createSvgElement("polyline", {
                class: "burnup-line burnup-line-scope",
                points: totalPoints,
            }));
            svg.appendChild(createSvgElement("polyline", {
                class: "burnup-line burnup-line-completed",
                points: completedPoints,
            }));

            const latest = sprint.points[pointCount - 1];
            [
                [latest.total, "burnup-point-scope"],
                [latest.completed, "burnup-point-completed"],
            ].forEach(([value, className]) => {
                svg.appendChild(createSvgElement("circle", {
                    class: `burnup-point ${className}`,
                    cx: xPosition(pointCount - 1),
                    cy: yPosition(value),
                    r: 5,
                }));
            });
        };

        const showSelectedSprint = () => {
            const selected = sprints.find((sprint) => String(sprint.id) === select.value) || sprints[0];
            renderBurnup(selected);
        };

        select.addEventListener("change", showSelectedSprint);
        showSelectedSprint();
    }
}
