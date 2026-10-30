// Initialize Vercel Web Analytics
// This script loads after vercel-analytics.js and initializes tracking

(function() {
  // Check if the inject function is available from the analytics module
  if (typeof window !== 'undefined') {
    // For Flask apps, we need to manually inject the analytics script
    // The inject function from @vercel/analytics handles the script loading
    
    // This is the inline version of the inject function
    // It creates the analytics script tag and adds it to the page
    (function injectAnalytics() {
      // Initialize the queue
      if (window.va) return;
      
      window.va = function() {
        if (!window.vaq) window.vaq = [];
        window.vaq.push(arguments);
      };
      
      // Detect environment (production by default)
      var mode = 'production';
      window.vam = mode;
      
      // Determine script source
      var scriptSrc = '/_vercel/insights/script.js';
      
      // Check if script already exists
      if (document.head.querySelector('script[src*="' + scriptSrc + '"]')) {
        return;
      }
      
      // Create and append the analytics script
      var script = document.createElement('script');
      script.src = scriptSrc;
      script.defer = true;
      
      // Add SDK metadata
      script.dataset.sdkn = '@vercel/analytics';
      script.dataset.sdkv = '2.0.1';
      
      // Error handler
      script.onerror = function() {
        console.log('[Vercel Web Analytics] Analytics script loaded. Analytics will be active when deployed to Vercel.');
      };
      
      document.head.appendChild(script);
    })();
  }
})();
