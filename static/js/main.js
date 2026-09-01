// ═══════════════════════════════════════════════════════════════════════════
// RITESH TOURS AND TRAVELS - Main JavaScript
// ═══════════════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', function() {

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Mobile nav toggle
    const navToggle = document.querySelector('.nav-toggle');
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            document.querySelector('.nav-links').classList.toggle('active');
        });
    }

    // Smooth scroll for internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

});

// Check seat availability via API (polling)
async function checkSeatAvailability(scheduleId) {
    try {
        const response = await fetch(`/api/seats/${scheduleId}`);
        const seats = await response.json();
        
        seats.forEach(seat => {
            const seatEl = document.querySelector(`.seat[data-seat="${seat.seat_number}"]`);
            if (seatEl && seat.is_booked && !seatEl.classList.contains('booked')) {
                seatEl.classList.add('booked');
                seatEl.classList.remove('selected');
                seatEl.onclick = null;
                seatEl.title = `Seat ${seat.seat_number} (Just Booked!)`;
                
                // Remove from selected if it was selected
                const idx = selectedSeats.indexOf(seat.seat_number);
                if (idx > -1) {
                    selectedSeats.splice(idx, 1);
                    updateBookingSummary();
                }
            }
        });
    } catch (err) {
        console.log('Could not check availability:', err);
    }
}
