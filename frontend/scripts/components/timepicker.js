export class EkiTimePicker {
  /**
   * Transforma un contenedor vacío en un Time Picker de ekiSystem.
   * @param {HTMLElement} container 
   * @param {Object} options 
   */
  constructor(container, options = {}) {
    this.container = container;
    this.name = options.name || container.dataset.name || 'time';
    this.defaultTime = options.defaultTime || container.dataset.default || '';
    
    this.hour = '';
    this.minute = '';

    if (this.defaultTime) {
      [this.hour, this.minute] = this.defaultTime.split(':');
    }

    this.render();
    this.setupEvents();
  }

  render() {
    this.container.innerHTML = `
      <div class="flex items-center gap-2">
        <div class="relative w-20">
          <select class="eki-hour-select w-full bg-surface border border-border-default text-text-primary rounded-xl px-3 py-2 text-center focus:outline-none focus:ring-2 focus:ring-accent transition-all cursor-pointer">
            <option value="" disabled ${!this.hour ? 'selected' : ''}>--</option>
            ${Array.from({length: 24}, (_, i) => {
              const val = i.toString().padStart(2, '0');
              return `<option value="${val}" ${this.hour === val ? 'selected' : ''}>${val}</option>`;
            }).join('')}
          </select>
        </div>
        
        <span class="text-text-tertiary font-bold">:</span>
        
        <div class="relative w-20">
          <select class="eki-minute-select w-full bg-surface border border-border-default text-text-primary rounded-xl px-3 py-2 text-center focus:outline-none focus:ring-2 focus:ring-accent transition-all cursor-pointer">
            <option value="" disabled ${!this.minute ? 'selected' : ''}>--</option>
            <option value="00" ${this.minute === '00' ? 'selected' : ''}>00</option>
            <option value="15" ${this.minute === '15' ? 'selected' : ''}>15</option>
            <option value="30" ${this.minute === '30' ? 'selected' : ''}>30</option>
            <option value="45" ${this.minute === '45' ? 'selected' : ''}>45</option>
          </select>
        </div>
      </div>
    `;
  }

  setupEvents() {
    this.hourSelect = this.container.querySelector('.eki-hour-select');
    this.minuteSelect = this.container.querySelector('.eki-minute-select');

    this.hourSelect.addEventListener('change', (e) => {
      this.hour = e.target.value;
      this.dispatchChange();
    });

    this.minuteSelect.addEventListener('change', (e) => {
      this.minute = e.target.value;
      this.dispatchChange();
    });
  }

  dispatchChange() {
    const event = new CustomEvent('change', { detail: this.getValue() });
    this.container.dispatchEvent(event);
  }

  getValue() {
    if (this.hour && this.minute) {
      return `${this.hour}:${this.minute}`;
    }
    return null;
  }

  disable() {
    this.hourSelect.disabled = true;
    this.minuteSelect.disabled = true;
    this.container.classList.add('opacity-50', 'pointer-events-none');
  }

  enable() {
    this.hourSelect.disabled = false;
    this.minuteSelect.disabled = false;
    this.container.classList.remove('opacity-50', 'pointer-events-none');
  }
}
