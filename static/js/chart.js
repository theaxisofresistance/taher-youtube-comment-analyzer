const ctx = document.getElementById('sentimentChart');

if (ctx) {
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Negative'],
            datasets: [{
                data: [sentimentData.positive, sentimentData.negative],
                backgroundColor: ['#22c55e', '#ef4444'],
                borderColor: '#181818',
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#f1f1f1'
                    }
                }
            }
        }
    });
}
