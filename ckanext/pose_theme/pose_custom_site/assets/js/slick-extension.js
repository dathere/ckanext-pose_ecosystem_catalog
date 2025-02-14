$(document).ready(function(){
	console.log('slick site');
	$('.slick-site').slick({
	  arrows: true,
	  autoplay: false,
	  autoplaySpeed: 5000,
	  lazyLoad: 'ondemand',
	  slidesToShow: 4,
	  slidesToScroll: 4,
	  responsive: [
		{
		  breakpoint: 1280,
		  settings: {
			slidesToShow: 3,
			slidesToScroll: 3
		  }
		},
		{
		  breakpoint: 980,
		  settings: {
			slidesToShow: 2,
			slidesToScroll: 2
		  }
		},
		{
		  breakpoint: 640,
		  settings: {
			slidesToShow: 1,
			slidesToScroll: 1
		  }
		}
	  ]
	});
  });