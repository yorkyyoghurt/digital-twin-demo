function test_EIT(data_path)

clc;
%% Set project folder
project_folder = fileparts(mfilename('fullpath'));

cd(project_folder);

%% Load configuration
run("config.m");

%% Start EIDORS
run(fullfile(eidors_folder, "startup.m"));

%% Load EIT data

[vv, auxdata] = eidors_readdata(data_path, 'eit');

%% Calculate frame rate

FR = 1/(median(diff(auxdata.t_rel))*1e-6);

fprintf('Frame rate: %.2f frames/s\n', FR);

%% Create EIT model

skip5 = {32,1,[0,5],[0,5],{'no_meas_current_next1'},1};

fmdl = mk_library_model('adult_male_32el');

[fmdl.stimulation,fmdl.meas_select] = ...
    mk_stim_patterns(skip5{:});

%% Create GREIT reconstruction model

opt.imgsz = [32 32];
opt.square_pixels = true;
opt.noise_figure = 0.5;

imdl = mk_GREIT_model( ...
    mk_image(fmdl,1), ...
    0.20, [], opt);

%% Reconstruct EIT data
vh = mean(vv(:,790:810),2);

imgr = inv_solve(imdl, vh, vv);

%% Convert reconstruction to images
imgs = -calc_slices(imgr);
imgs(isnan(imgs)) = 0;

%% Display first reconstructed image
figure;
imagesc(real(imgs(:,:,1)));
axis equal;
axis off;
colorbar;
title('EIT reconstruction');

%% Display multiple reconstructed frames

figure;

for i = 1:10
    subplot(2,5,i);
    imagesc(real(imgs(:,:,i)));
    axis equal;
    axis off;
    colorbar;
    title(sprintf('Frame %d', i));
end

%% Save reconstructed EIT data for Python

time = auxdata.t_rel * 1e-6;

save('EIT_reconstructed.mat', 'imgs', 'time');
end