ckan.module('dqs-form', function ($, _) {
  "use strict";
  return {
    options: {
    },

    statuses: ['Poor', 'Poor', 'Fair', 'Good', 'Very Good', 'Excellent', 'Excellent'],

    initialize: function () {
      $.proxyAll(this, /_on/);
      this._score = $('#dqs-score');
      this._checkbox = $('.dqs-tick');
      this._checkbox.on('change', this._checkboxChange);
      this.el.on('change', this._onChange);

      this._qb = this.$('.quality-block');
      this._qr = this.$('.quality-results .dqs-bar');
      this.rating = this.$('.quality-results .dqs-rating');
      this.res_stat = this.$('#result-status');
      this.gr_rating = this.$('.quality-block .group-rating');
      this._onChange();
    },

    _onChange: function(e) {
      var checked = this.$(':checked');
      this._score.text(checked.length);
      this.res_stat.text(this.statuses[Math.ceil((checked.length+1)/5)])
      // handle either checkbox change or page load
      this._recalculateStats(e ? $(e.target) : this._qb.find(':checkbox:first'));
    },
    _checkboxChange: function(e) {
      $('.seed-export-dqs-btn a').attr('disabled', 'disabled')
        .attr('title', 'Export disabled. Please save the changes in order to enable it or reload the page.');
      $('.seed-export-dqs-btn a').on('click', function(event) {
        event.preventDefault();
        return false;
      });
    },
    _recalculateStats: function(targets) {
      for (var k = 0; k < targets.length; k++) {
        var i = Math.ceil(targets.eq(k).attr('name').slice(2) / 5) - 1;
        var sectionProgress = this._qb.eq(i).find(':checked').length;
        this._qr.eq(i).attr('data-progress', sectionProgress);
        this.rating.eq(i).text(this.statuses[sectionProgress]);
        this.gr_rating.eq(i).html('(<span>'+sectionProgress+'</span>)');   
      }
    }
  };
});
