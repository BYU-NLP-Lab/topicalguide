/* From http://www.sohtanaka.com/web-design/fancy-thumbnail-hover-effect-w-jquery/ */
function image_preview() {
	$("ul.analyses li img.plot").hover(function() {
		$(this).css({'z-index' : '10'}); /*Add a higher z-index value so this image stays on top*/ 
		$(this).addClass("hover").stop() /* Add class of "hover", then stop animation queue buildup*/
			.animate({
				marginTop: '-160px', /* The next 4 lines will vertically align this image */ 
				marginLeft: '-160px',
				top: '50%',
				left: '50%',
				width: '274px', /* Set new width */
				height: '274px', /* Set new height */
				padding: '20px'
			}, 200); /* this value of "200" is the speed of how fast/slow this hover animates */

		} , function() {
		$(this).css({'z-index' : '0'}); /* Set z-index back to 0 */
		$(this).removeClass("hover").stop()  /* Remove the "hover" class , then stop animation queue buildup*/
			.animate({
				marginTop: '0', /* Set alignment back to default */
				marginLeft: '0',
				top: '0',
				left: '0',
				width: '150px', /* Set width back to default */
				height: '150px', /* Set height back to default */
				padding: '5px'
			}, 400);
	});
}