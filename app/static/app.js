document.addEventListener("submit", (event) => {
    const message = event.target.dataset.confirm;

    if (message && !window.confirm(message)) {
        event.preventDefault();
    }
});

const board = document.querySelector("[data-task-board]");

if (board) {
    let draggedCard = null;
    let dragPreview = null;
    const statusMessage = document.querySelector(".drag-status");
    const dropIndicator = document.createElement("div");
    dropIndicator.className = "task-drop-indicator";
    dropIndicator.setAttribute("aria-hidden", "true");

    const clearDropState = () => {
        board.querySelectorAll("[data-drop-zone].is-drag-over").forEach((zone) => {
            zone.classList.remove("is-drag-over");
        });
        dropIndicator.remove();
    };

    const findInsertionTarget = (dropZone, pointerY) => {
        return [...dropZone.querySelectorAll("[data-task-id]")]
            .filter((candidate) => candidate !== draggedCard)
            .find((candidate) => {
                const bounds = candidate.getBoundingClientRect();
                return pointerY < bounds.top + bounds.height / 2;
            });
    };

    board.addEventListener("dragstart", (event) => {
        const card = event.target.closest("[data-task-id]");
        if (!card) return;
        if (event.target.closest("a, button, input, select, textarea")) {
            event.preventDefault();
            return;
        }

        draggedCard = card;
        card.classList.add("is-dragging");
        card.setAttribute("aria-grabbed", "true");
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", card.dataset.taskId);

        const cardBounds = card.getBoundingClientRect();
        dragPreview = card.cloneNode(true);
        dragPreview.classList.remove("is-dragging", "is-updating");
        dragPreview.classList.add("task-drag-preview");
        dragPreview.style.width = `${cardBounds.width}px`;
        dragPreview.removeAttribute("draggable");
        dragPreview.querySelectorAll("a, button, input, select, textarea").forEach((control) => {
            control.setAttribute("tabindex", "-1");
        });
        document.body.appendChild(dragPreview);
        event.dataTransfer.setDragImage(
            dragPreview,
            Math.min(Math.max(event.offsetX, 24), cardBounds.width - 24),
            Math.min(Math.max(event.offsetY, 20), cardBounds.height - 20),
        );
    });

    board.addEventListener("dragend", () => {
        draggedCard?.classList.remove("is-dragging");
        draggedCard?.removeAttribute("aria-grabbed");
        dragPreview?.remove();
        dragPreview = null;
        clearDropState();
        draggedCard = null;
    });

    board.addEventListener("dragover", (event) => {
        const column = event.target.closest("[data-status]");
        if (!column || !draggedCard) return;

        event.preventDefault();
        event.dataTransfer.dropEffect = "move";
        clearDropState();
        const dropZone = column.querySelector("[data-drop-zone]");
        dropZone?.classList.add("is-drag-over");

        if (dropZone) {
            const insertionTarget = findInsertionTarget(dropZone, event.clientY);
            const emptyState = dropZone.querySelector(".column-empty");
            dropZone.insertBefore(dropIndicator, insertionTarget || emptyState);
        }
    });

    board.addEventListener("dragleave", (event) => {
        const dropZone = event.target.closest("[data-drop-zone]");
        if (dropZone && !dropZone.contains(event.relatedTarget)) {
            dropZone.classList.remove("is-drag-over");
        }
    });

    board.addEventListener("drop", async (event) => {
        const column = event.target.closest("[data-status]");
        if (!column || !draggedCard) return;

        event.preventDefault();
        clearDropState();
        const card = draggedCard;
        const newStatus = column.dataset.status;

        const formData = new FormData();
        formData.set("status", newStatus);
        const startingBounds = card.getBoundingClientRect();
        const targetList = column.querySelector("[data-drop-zone]");
        const insertionTarget = findInsertionTarget(targetList, event.clientY);

        targetList.querySelector(".column-empty")?.remove();
        if (insertionTarget) {
            targetList.insertBefore(card, insertionTarget);
        } else {
            targetList.appendChild(card);
        }

        targetList.querySelectorAll("[data-task-id]").forEach((taskCard) => {
            formData.append("ordered_task_ids", taskCard.dataset.taskId);
        });
        card.classList.remove("is-dragging");
        card.removeAttribute("aria-grabbed");
        card.classList.add("is-updating");

        const endingBounds = card.getBoundingClientRect();
        const settleAnimation = card.animate(
            [
                {
                    transform: `translate(${startingBounds.left - endingBounds.left}px, ${startingBounds.top - endingBounds.top}px)`,
                    opacity: 0.72,
                },
                { transform: "translate(0, 0)", opacity: 1 },
            ],
            { duration: 220, easing: "cubic-bezier(0.22, 1, 0.36, 1)" },
        );

        try {
            const response = await fetch(card.dataset.statusUrl, {
                method: "POST",
                body: formData,
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });

            if (!response.ok) throw new Error("Status update failed");

            statusMessage.textContent = `Task moved to ${newStatus}.`;
            await settleAnimation.finished.catch(() => {});
            window.location.reload();
        } catch (error) {
            card.classList.remove("is-updating");
            statusMessage.textContent = "The task could not be moved. Please try dragging it again.";
            window.alert(statusMessage.textContent);
            window.location.reload();
        }
    });
}

const burnupChart = document.querySelector("[data-burnup-chart]");

if (burnupChart) {
    const dataElement = burnupChart.querySelector("[data-burnup-data]");

    if (dataElement) {
        const burnup = JSON.parse(dataElement.textContent);
        const svg = burnupChart.querySelector("[data-burnup-svg]");
        const emptyState = burnupChart.querySelector("[data-burnup-empty]");
        const legend = burnupChart.querySelector(".burnup-legend");
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

        const renderBurnup = () => {
            svg.replaceChildren();
            const hasChartData = burnup.total_points > 0 && burnup.points.length > 0;
            svg.toggleAttribute("hidden", !hasChartData);
            emptyState.hidden = hasChartData;
            legend.hidden = !hasChartData;

            if (!hasChartData) {
                return;
            }

            const width = 800;
            const height = 300;
            const padding = { top: 20, right: 22, bottom: 42, left: 54 };
            const plotWidth = width - padding.left - padding.right;
            const plotHeight = height - padding.top - padding.bottom;
            const maxPoints = Math.max(
                burnup.total_points,
                ...burnup.points.map((point) => Math.max(point.total, point.completed)),
                1,
            );
            const pointCount = burnup.points.length;
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
                label.textContent = formatChartDate(burnup.points[index].date);
                svg.appendChild(label);
            });

            const totalPoints = burnup.points
                .map((point, index) => `${xPosition(index)},${yPosition(point.total)}`)
                .join(" ");
            const completedPoints = burnup.points
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

            const latest = burnup.points[pointCount - 1];
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

        renderBurnup();
    }
}
