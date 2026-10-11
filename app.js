// Función para cargar el reporte detallado por día
async function cargarReporteDiario() {
    try {
        const respuesta = await fetch('/api/reportes/diario');
        const data = await respuesta.json();
        const tbody = document.getElementById('tablaReporteDiario');
        
        tbody.innerHTML = ''; // Limpiar tabla antes de llenarla

        data.reporte_diario.forEach(fila => {
            const tr = document.createElement('tr');
            
            // Formatear el dinero a pesos colombianos
            const dineroFormateado = '$' + fila.total.toLocaleString('es-CO');
            
            tr.innerHTML = `
                <td><strong>${fila.fecha}</strong></td>
                <td><span class="badge bg-secondary">${fila.sitio}</span></td>
                <td class="text-end text-success fw-bold">${dineroFormateado}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error("Error cargando el reporte diario:", error);
    }
}

// Asegúrese de llamar a esta función cuando cargue la página
window.onload = function() {
    cargarDashboard(); // La función que ya tenía para las gráficas y resúmenes
    cargarReporteDiario(); // La nueva función para la tabla
};
