$(document).ready(function() {
	var $clouds = $('#word-cloud .cloud');
	$clouds.filter(':not(:first)').hide();
	$('#id_cloud_type').change(function() {
		$clouds.hide();
		var cloud_name = $(this).val();
		$clouds.filter('#id_cloud_' + cloud_name).show();
	});
});
